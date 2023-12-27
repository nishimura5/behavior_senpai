export PYTHON_HOME="/Library/Frameworks/Python.framework/Version/3.11.6/bin"
export PATH="$PYTHON_HOME:$PATH"
alias python='python3'
alias pip='pip3'

. .venv/bin/activate
python ./src/launcher.py