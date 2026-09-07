.PHONY: install build app test clean
install: ; pip install -r requirements.txt
build:   ; python run_all.py
app:     ; streamlit run app/app.py
test:    ; PYTHONPATH=. pytest tests/ -q
clean:   ; rm -f artifacts/engagement360.sqlite; rm -rf artifacts/model/* artifacts/powerbi/*
