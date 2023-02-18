
VENV_NAME=venv
PYTHON=python3
REQUIREMENTS=requirements.txt

$(VENV_NAME)/bin/activate: $(REQUIREMENTS)
	test -d $(VENV_NAME) || $(PYTHON) -m venv $(VENV_NAME)
	. $(VENV_NAME)/bin/activate && pip install -U pip
	. $(VENV_NAME)/bin/activate && pip install -r $(REQUIREMENTS)
	touch $(VENV_NAME)/bin/activate

run: $(VENV_NAME)/bin/activate
	. $(VENV_NAME)/bin/activate && $(PYTHON) ote_dump.py

clean:
	rm -rf $(VENV_NAME)
