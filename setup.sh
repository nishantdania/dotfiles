#! /usr/bin/zsh

if [ ! -f ~/.vimrc ]; then
  echo "Linking vimrc..."
  ln -s ~/Code/dotfiles/.vimrc ~/.vimrc
fi

if [ ! -f ~/.tmux.conf ]; then
  echo "Linking tmux config..."
  ln -s ~/Code/dotfiles/.tmux.conf ~/.tmux.conf
fi

echo "Installing ripgrep..."
paru --noconfirm -S ripgrep

if [ ! -d ~/.fzf ]; then
  echo "Installing fzf..."
  git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
  ~/.fzf/install
fi

echo "Installing tmux..."
paru --noconfirm -S tmux

echo "Installing xsel"
paru --noconfirm -S xsel

if [ ! -d ~/.oh-my-zsh ]; then
  echo "Installing Oh-My-Zsh"
  cd ~
  wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh
  cd ~/Code
fi

rm ~/.zshrc
cat ~/.oh-my-zsh/templates/zshrc.zsh-template >> ~/.zshrc

echo "Setup aliases"
echo "alias pbcopy=\"xsel --clipboard --input\"" >> ~/.zshrc
echo "alias pbpaste=\"xsel --clipboard --output\"" >> ~/.zshrc
echo "alias vi=\"vim\"" >> ~/.zshrc
source ~/.zshrc

echo "Setup git user"
git config --global user.email "nishantdania@gmail.com"
git config --global user.name "nishantdania"

# if [ -z "${DISPLAY}" ] && [ "${XDG_VTNR}" -eq 1 ]; then
#  exec startx
#fi

