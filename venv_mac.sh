export PYTHON_HOME="/Library/Frameworks/Python.framework/Version/3.11.6/bin"
export PATH="$PYTHON_HOME:$PATH"
alias python='python3'
alias pip='pip3'
python -m venv --prompt behavior-senpai .venv
. .venv/bin/activate
pip install torch~=2.1
pip install ultralytics~=8.0
pip install lapx~=0.5.4
pip install mediapipe~=0.10
pip install scikit-learn~=1.3
pip install pyperclip~=1.8
