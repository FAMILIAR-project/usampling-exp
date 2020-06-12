git clone https://github.com/maxcordy/SPLConqueror.git
cd SPLConqueror
git submodule update --init --recursive
apt-get update
apt install mono-complete monodevelop
apt install nuget
cd SPLConqueror/
nuget restore
cd SPLConqueror/
xbuild SPLConqueror_Core.csproj
cd ../MachineLearning
xbuild MachineLearning.csproj
cd ../CommandLine
xbuild CommandLine.csproj
cd bin/Debug
wget https://github.com/Z3Prover/z3/releases/download/z3-4.8.7/z3-4.8.7-x64-ubuntu-16.04.zip
unzip z3-4.8.7-x64-ubuntu-16.04.zip
cp z3-4.8.7-x64-ubuntu-16.04/bin/* .