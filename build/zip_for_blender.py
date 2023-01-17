# This file must be run from the repository root.

projectName = "mouse_strafing"
additionalDirectories = []
additionalFiles = ["LICENSE"]

def getVersion():
	import re
	with open("__init__.py", mode="r") as f:
		m = re.compile(r"""^\s*"version"\s*:\s*\(\s*(?P<major>\d+)\s*,\s*(?P<minor>\d+)\s*(,\s*(?P<patch>\d+)\s*)?\)\s*,?\s*$""", re.MULTILINE).search(f.read())
		if m.group("patch") != None:
			return f'{m.group("major")}.{m.group("minor")}.{m.group("patch")}'
		else:
			return f'{m.group("major")}.{m.group("minor")}'

if __name__ == "__main__":
	import zipfile
	from pathlib import Path
	zipFileName = f"{projectName}-{getVersion()}.zip"
	print(f"Writing {zipFileName}...")
	with zipfile.ZipFile(zipFileName, "w", zipfile.ZIP_DEFLATED) as zf:
		for dir in additionalDirectories:
			for path in Path(dir).rglob("*"):
				print(f"Adding {path} as {path.as_posix()}")
				zf.write(path, path.as_posix())
		for path in Path(".").glob("*.py"):
			print(f"Adding {path} as {path.as_posix()}")
			zf.write(path, path.as_posix())
		for fileName in additionalFiles:
			print(f"Adding {fileName} as {fileName}")
			zf.write(fileName, fileName)
