# create venv
python3 -m venv ai-agents-sms
source ai-agents-sms/bin/activate
# install requirements
pip install -r requirements.txt
# ensure you have your environment variables set + exported
        # OPENAI_API_KEY= XXXX
        # OPENAI_ORG_ID=XXX
        # DB_HOST=XXX
        # DB_PORT=XXX
        # DB_USER=XXX
        # DB_PASSWORD=XXX
        # DB_NAME=XXX
        # TWILIO_AUTH_TOKEN=XXX
        # TWILIO_PHONE_NUMBER=XXX
        # TWILIO_ACCOUNT_SID=XXX
        # PERSONAL_PHONE_NUMBER=XXX

#in addition to twilio config, you must ensure you have an approved brand, campaign and 
#message service set up (can take 2-3 days for approval)

#If this is your first time setting up the database schema you can run
python3 reset_db.py

#If this is your first time setting up an Agent you can run configure your agent
#prompt details in create_agent.py and run
python3 create_agent.py 

#To host locally you can follow the instructions below.
#open a new shell and 
#set up ngrok as port forwarding
ngrok http 8000 

# copy the ngrok url 
# ex. https://72fa-2603-3020-1823-8b00-80eb-604f-6d0b-8f1f.ngrok-free.app 

# paste into twilio phone number MESSAGING configuration to host the sms endpoint
# https://72fa-2603-3020-1823-8b00-80eb-604f-6d0b-8f1f.ngrok-free.app/sms 
# save new configuration 

#open a new shell and 
#run api locally
uvicorn main:app --reload

#open a new shell and run test file to
# invoke generate-text and send-initial text endpoints 
python3 test_sms.py

#you should receive a message from the twilio phone number
#by responding to it you will invoke the /sms endpoint that is hosted on twilio 
#you can see in the logs if there are any 500 errors 
#also leverage DB logs for debugging 
#select * from journeymanai.SMS_Logs 

#since API is being run in debug mode you will be able to make change to the prompt (in the DB) or changes to
#the API code in python - and the API will refresh, meaning you can debug live.


#If you wish to deploy this on an EC2 server you can ssh into your server, clone the repo and run
sudo docker-compose up -d --build

#this should host the SMS APIs so you can invoke them from elsewhere 
#now you can put your public IP directly into Twilio 
