You can test custom model downloading in your local machine.

```sh
pip install pytest coverage
cd ..

coverage run --source muse -m pytest muse tests/test_custom_model_using_local_path.py -v -s
coverage run --source muse -m pytest muse tests/test_custom_model_using_http_url.py -v -s
```
