pip install -r requirements.txt
pip install -r requirements/dev.txt
git clone -b rel/pl_18 https://github.com/rohitgr7/stable-diffusion
pip install -r stable-diffusion/requirements.txt
pip install -e stable-diffusion
pip install git+https://github.com/rohitgr7/lightning-flash.git@rel/pl_18#egg=lightning-flash[text]
