import os
import re
import requests
import tarfile

release_api_url = os.environ["RELEASE_API_URL"]
github_token = os.environ["GITHUB_TOKEN"]
issue_module = os.environ["ISSUE_MODULE"]
issue_version = os.environ["ISSUE_VERSION"]

response = requests.get(
  release_api_url,
  headers={
    "Content-Type": "application/vnd.github.v3.raw+json",
    "Authorization": f"token {github_token}"
  }
)
if (200 <= response.status_code < 300) is False:
  print(f"Release meta-data could not be fetched from {release_api_url} (error {response.status_code}")
  exit(1)

matching_releases = list(filter(lambda x: (x["tag_name"] == issue_version), response.json()))
if len(matching_releases) == 0:
  print(f"Release {issue_version} not found")
  exit(1)
release_data = matching_releases[0]
issue_asset_file = f"{issue_module}-{issue_version}.tar.gz"
release_slug = None

asset_filename_pattern = re.compile(r"(.*)-([0-9]+\.[0-9]+\.[0-9]+)\.tar\.gz")
for asset_data in release_data["assets"]:
  asset_download_url = asset_data["browser_download_url"]
  
  asset_file = asset_data["name"]
  asset_file_match = asset_filename_pattern.match(asset_file)
  if (asset_file_match is None) or (asset_file_match[1] != issue_module):
    print(f"Skipping unknown Release Asset: {asset_file} (expecting {asset_file_match[1]} but got {issue_module}")
    continue
  asset_package_name = asset_file_match[1]
  asset_package_version = asset_file_match[2]

  if asset_package_version != issue_version:
    print(f"Version in Release Asset filename ({asset_package_version}) and requested version ({issue_version}) did not match.")
    exit(1)

  os.makedirs("dist", exist_ok=True)

  release_slug = f"{asset_package_name}-{asset_package_version}"

  tar_file = f"dist/{release_slug}.tar.gz"
  print(f"Downloading Release Asset {asset_file} to {tar_file}")
  download_response = requests.get(
    asset_download_url,
    headers={
      "Authorization": f"token {github_token}"
    }
  )
  with open(tar_file, "wb") as f:
    f.write(download_response.content)

  downloaded_asset_size = os.lstat(tar_file).st_size
  expected_asset_size = asset_data["size"]
  if downloaded_asset_size != expected_asset_size:
    print(f"Release Asset size mismatch. Downloaded {downloaded_asset_size}, but expected {expected_asset_size} bytes")
    exit(1)

  with tarfile.open(tar_file, "r:gz") as tar:
    for member in tar.getmembers():
      if (member.name.startswith(release_slug) is False) or (".." in member.name):
        print(f"Release asset file content mismatch. Illegal path {member.name}")
        exit(1)

      file_name = member.name[len(release_slug)+1:]
      source_file_path = f"./source/{file_name}"

      if file_name == "PKG-INFO":
        continue
      
      if (os.path.basename(file_name) == ".version") and os.path.isdir(os.path.dirname(source_file_path)):
        continue

      if member.isdir() is True:
        if os.path.isdir(source_file_path) is False:
          path(f"Source directory {file_name} does not exist.")
          exit(1)
        else:
          continue

      if os.path.isfile(source_file_path) is False:
        print(f"Source file {file_name} does not exist in version control.")

      with tar.extractfile(member) as file_a:
        with open(source_file_path, "rb") as file_b:
          A = file_a.read()
          B = file_b.read()
          print(A)
          print("---")
          print(B)
          if A != B:
            print(f"Source file {file_name} content mismatch.")
            exit(1)

      print(f"Release Asset {tar_file} content matches source repository.")
      print(f"::set-output name=TARFILE::{tar_file}")
      exit(0)

print(f"Could not find Release Asset: {issue_asset_file}")
exit(1)
