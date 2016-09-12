export DH_UPGRADE_PIP=8.0.03
export DH_UPGRADE_SETUPTOOLS=23.0
dpkg-buildpackage -us -uc -I.hg -i.hg -Imodules -Iexternal -Idata -Ibqcore/bq/core/public/extjs -Itools
