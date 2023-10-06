#!/usr/bin/env bash
set -e

python3 --version
is_310_or_later=$(python3 -c 'import sys; print(str(sys.version_info[1] >= 10))')

if [[ "${is_310_or_later}" == "False" ]]; then
    apt install --yes python3.10 python3.10-distutils python3.10-venv curl
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 2
    update-alternatives --set python3 /usr/bin/python3.10
else
    apt install --yes python3-distutils python3-venv python3-pip curl
fi

python3 --version
