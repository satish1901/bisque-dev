#### Version Control Instructions (HG-GIT)

Maintain the HG->GIT code push using http://hg-git.github.io

- Current Release Version: [0.5.10](https://biodev.ece.ucsb.edu/hg/bisque-stable/rev/0.5.10)
- Instructions  :https://til.secretgeek.net/mercurial/convert_hg_to_git.html
- Source HG     :https://biodev.ece.ucsb.edu/hg/bisque-stable
- Target Git    :https://github.com/UCSB-VRL/bisque.git

hg->git push

 - Install
  ```
  $ sudo easy_install hg-git 
  $ hg clone --insecure https://biodev.ece.ucsb.edu/hg/bisque-stable
  ```
 - Make sure the following is in your .hgrc file: vim ~/.hgrc
  ```
  [git]
  intree = 1
  [extensions]
  hgext.bookmarks =
  hggit = 
  [ui]
  ignore = ~/.hgignore
  ```
- Add a master branch name to the repo and export 
  ```
  cd bisque-stable 
  hg bookmark -r default master # so a ref gets created
  hg gexport --debug # exporting hg commits/objects to git
  ```
- Initialize and prepare the target git repo 
  ```
  git init
  git remote add origin https://github.com/UCSB-VRL/bisque.git
  git remote -v # verify the remote repo
  ```
- track the large files using LFS https://git-lfs.github.com/
  ```
  curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
  git lfs install
  git lfs track "*.ipch"
  git lfs track "*.sdf"
  git lfs track "*.sav"
  git lfs track "*.model"
  git add .gitattributes
  ```
- Check the commits using 'git status' and prepare for github
  ```
  git pull  origin master
  git add --all
  git commit -m "hg-git from  https://biodev.ece.ucsb.edu/hg/bisque-stable/"
  git push origin master
  ```


- Current Advice: Stare and compare that the new git repo matches the old hg repo, until you are completely satisfied.
