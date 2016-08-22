# LP (Language Processing)
## Leidos Visualisation Wizard Tools
**The Language Processing package provides language processing capabilities for Visualisation Wizard**

_Note this file provides instructions for cloning, setting up, then running the LP web services in a python virtual environment (sandbox). 
Using this approach will create the sandbox in a folder you choose_

### Install and setup procedure (for Windows). 

Set up the virtual environment (for Linux like environments, Ubuntu, macOS e.g. see [linux virtualenv setup](#linux-virtualenv) )

```
pip install virtualenv


cd <some place convenient on your file system>

mkdir env\data

set ENVHOME=<some place convenient on your file system>\env

cd %ENVHOME%

virtualenv env

set VENV=%ENVHOME%\env

%VENV%\Scripts\activate
```

Now you're operating entirely from within the virtual environment with no depedencies on and system installed python, etc.

Next, from the location of the project home / git clone-to location

Get the code repo

```
set PROJECTHOME=<git-project-clone-location>

cd %PROJECTHOME%

git clone https://<username>@issbu.git.cloudforge.com/digitaledge_viz_wizard.git
```
The Language Processing Project is now in place.

Next install all the libraries needed into the virtual environment

```
cd %PROJECTHOME%\digitaledge_viz_wizard\vizwiz-beta\language-processing-service\server

cp requirements.txt %ENVHOME%

cp *.whl %ENVHOME%

cd %ENVHOME%

pip install -r requirements.txt
```

This should satisfy all the project's requirements for libraries and dependencies


###  WSGI webserver startup:



```
cd %PROJECTHOME%\digitaledge_viz_wizard\vizwiz-beta\language-processing-service\server

pip install -e  .

pserve development.ini –reload

```


The --reload option runs a file monitor such that any time you edit and save any of the significant files, the server will reload

_Note this file can be read with the standalone grip reader. To install do_

```
pip3 install grip
```


#linux-virtualenv

### Install and setup procedure (for Linux like environments). 

For Linux and macOS, the procedure is similar but has its own peculiarities

```
cd <folder for which you have read-write-execute priviliges>
export VENVHOME=<folder for which you have read-write-execute priviliges>

mkdir -p ENV/data

pip install virtualenv

virtualenv ENV

export VENV=/Users/danamoore/ENV

$VENV/bin/activate
```
 
 From here one can proceed to satisfy the requirements 
  
 Next install all the libraries needed into the virtual environment

```
cd %PROJECTHOME%/digitaledge_viz_wizard/vizwiz-beta/language-processing-service/server

cp requirements.txt $VENV/data

cp *.whl $VENV/data

cd $VENV/data

pip install -r requirements.txt
```

This should satisfy all the project's requirements for libraries and dependencies 