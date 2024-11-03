# Modrinth Mod Download
A great utility for bulk downloading modrinth mods using the modrinth API. <br>
Note that this utility was made for **Linux**, specifically **Debian Testing (13/Trixie) Linux**.

## Requirements
- python3-termcolor

## Usage
### Using Python3
```bash
cd ./path/to/modrinth-downloader
python3 ./download.py ./path/to/modlist.yaml
```
### Using ./download.sh and ./modlists
- First create a folder in the modrinth-downloader named **exactly** `modlists`.
- Then add modlists with file type **yaml** inside.
```bash
cd ./path/to/modrinth-downloader

# if chmod is available (probably any linux distro)
chmod +x ./download.sh # to give shell script execute permissions
./download.sh name-of-modlist # without the .yaml file extension
```