ARG arg_ubuntu_version=20.04

FROM ubuntu:${arg_ubuntu_version}

ARG arg_gcc_version=10
ENV gcc_version=${arg_gcc_version}

RUN apt-get update --yes && apt-get install --yes software-properties-common
RUN add-apt-repository --yes --update ppa:ubuntu-toolchain-r/test && add-apt-repository ppa:deadsnakes/ppa && apt-get update --yes

RUN apt-get install -y --no-install-recommends build-essential cmake git \
            libasound2-dev libgtk2.0-dev libjack-jackd2-dev gettext libgl1-mesa-dev uuid-dev oss4-dev \
            libx11-dev libx11-xcb-dev libfontenc-dev libice-dev libsm-dev libxau-dev \
            libxaw7-dev libxcomposite-dev libxcursor-dev libxdamage-dev libxdmcp-dev libxext-dev \
            libxfixes-dev libxi-dev libxinerama-dev libxkbfile-dev libxmu-dev libxmuu-dev \
            libxpm-dev libxrandr-dev libxrender-dev libxres-dev libxss-dev libxt-dev libxtst-dev \
            libxv-dev libxvmc-dev libxxf86vm-dev libxcb-render0-dev libxcb-render-util0-dev \
            libxcb-xkb-dev libxcb-icccm4-dev libxcb-image0-dev libxcb-keysyms1-dev \
            libxcb-randr0-dev libxcb-shape0-dev  libxcb-sync-dev libxcb-xfixes0-dev \
            libxcb-xinerama0-dev libxcb-dri3-dev libxcb-util0-dev libxcb-cursor-dev xkb-data m4 \
    && apt-get remove -y ccache

RUN apt install --yes gcc-${arg_gcc_version} g++-${arg_gcc_version} &&\
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-${arg_gcc_version} 100 &&\
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-${arg_gcc_version} 100 &&\
    update-alternatives --install /usr/bin/gcov gcov /usr/bin/gcov-${arg_gcc_version} 100 &&\
    update-alternatives --set gcc /usr/bin/gcc-${arg_gcc_version} &&\
    update-alternatives --set g++ /usr/bin/g++-${arg_gcc_version} &&\
    update-alternatives --set gcov /usr/bin/gcov-${arg_gcc_version}

RUN if [[ "${arg_ubuntu_version}" -lt "22.04" ]] ; then \
        apt install --yes python3.10 python3.10-distutils python3.10-venv curl &&\
        update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 && \
        update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 2 && \
        update-alternatives --set python3 /usr/bin/python3.10; \
    else \
        apt install --yes python3-distutils python3-venv python3-pip curl; \
    fi

RUN groupadd -r user && useradd -r -g user user
RUN mkdir -p /home/user && chown -R user:user /home/user
USER user

WORKDIR /build

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

ENV PATH="/home/user/.local/bin:${PATH}"

COPY [".env", "/build/.env"]
COPY ["docker_build.sh", "/build/docker_build.sh"]

ARG arg_recipes_repo=https://github.com/audacity/conan-recipes.git
ARG arg_recipes_branch=master
ARG arg_audacity_repo=https://github.com/audacity/audacity.git
ARG arg_audacity_branch=master
ARG arg_upload_build_tools=false
ARG arg_build_order=build_order.yml
ARG arg_build_config=audacity3

ENV recipes_repo=${arg_recipes_repo}
ENV recipes_branch=${arg_recipes_branch}
ENV audacity_repo=${arg_audacity_repo}
ENV audacity_branch=${arg_audacity_branch}
ENV upload_build_tools=${arg_upload_build_tools}
ENV build_order=${arg_build_order}
ENV build_config=${arg_build_config}

ENTRYPOINT ["bash", "-ex", "/build/docker_build.sh"]
