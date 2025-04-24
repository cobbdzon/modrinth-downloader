# Modrinth Mod Download

A great utility for bulk downloading Modrinth mods using the Modrinth API. <br>
Note that this utility was made for **Linux**, specifically **Debian Testing (13/Trixie) Linux**.

## Usage

### Installation
```bash
python3 -m venv .venv
source .venv/bin/activate # activate virtual environment
pip install -r requirements.txt # installs required packages into virtual environment
```

### Writing Modlists

See `examples` folder for a full example

```yaml
modlist_name: "test-modlist" # no spaces

# if not declared, both of these will default to the config.yaml
minecraft_version: "1.21"
mod_loader: "fabric"

client:
  - sodium@mc1.20.1-0.5.11

shared:
  - tough-as-nails

server:
  - noisium
```

#### Using version selectors

For this example, check out [sodium's versions page](https://modrinth.com/mod/sodium/versions). Version selectors are the `name` column of the version list. If you are going to select verion `mc1.20.1-0.5.11`, add the entry `sodium@mc1.20.1-0.5.11` in the client scope of the modlist.

### Using Python3

```bash
cd /path/to/modrinth-downloader
source .venv/bin/activate # activate virtual environment
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

## Plans

- Adding support for Windows (help is welcome from any Windows user)
- Turn project into a pip package.
- Make it into a package-esque version management system. (Similar to apt in Debian Linux)
