# Ethstakers.club Setup Guide
This guide will walk you through the setup process for the Ethstakers.club Beacon Explorer on your local machine.

## Prerequisites
Before proceeding with the installation, make sure you have the following prerequisites installed on your machine:

- Python 3
- Virtualenv (python3-venv)
- pip (python3-pip)
- libpq-dev
- PostgreSQL
- PostgreSQL-contrib

To install these prerequisites on Ubuntu, run the following commands:
```bash
sudo apt update
sudo apt install python3-venv python3-pip libpq-dev postgresql postgresql-contrib
sudo systemctl start postgresql.service
```

In addition to this you need:
- a fully synced beacon archive node
e.g. you can launch lighthouse using `--http --slots-per-restore-point 128 --disable-backfill-rate-limiting --genesis-backfill --historic-state-cache-size 4 --reconstruct-historic-states`.
This needs ~2.5TB of storage (HDD storage is good enough for the freezer_db).
- a synced execution client (e.g. geth, ...)
- ~1 TB of SSD storage for the postgres database
- time as it took (as of July 2023) 3 days to sync the beacon archive node and an additional 5 days to sync the actual explorer (on a 38€ server). Although, more cores and a faster storage such as NVMe should speed this up significantly.

## Installation
Follow the steps below to install and set up the Ethstakers.club Explorer:

### Create a Python virtual environment:
```bash
python3 -m venv .venv/ethstakersclub
```

### Activate the virtual environment:
```bash
source .venv/ethstakersclub/bin/activate
```

### Clone the ethstakersclub repository:
```bash
git clone https://github.com/ethstakersclub/ethstakersclub.git
cd ethstakersclub
```

### Install the required Python packages:
```bash
pip3 install -r requirements.txt
```

for the captcha you also need:
```bash
sudo apt-get install libz-dev libjpeg-dev libfreetype6-dev python-dev-is-python3
```

### Set up the PostgreSQL database:
```bash
sudo -u postgres psql
```

Inside the PostgreSQL shell, execute the following commands.

Change the following values as needed:
- password (myproject_database_password)
- user name (myproject_user)
- and db name (ethstakersclub)

```sql
CREATE DATABASE ethstakersclub;
CREATE USER myproject_user WITH PASSWORD 'myproject_database_password';
ALTER ROLE myproject_user SET client_encoding TO 'utf8';
ALTER ROLE myproject_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE myproject_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ethstakersclub TO myproject_user;
ALTER DATABASE ethstakersclub OWNER TO myproject_user;
```

Exit the PostgreSQL shell by typing \q or exit.

### Settings
To configure the development settings, you need to copy the `settings.py.example` file to `settings.py` and update the values accordingly. Use the command below to accomplish this:
```bash
cp settings.py.example settings.py
```

After copying the file, open `settings.py` in a text editor and modify the necessary values to match your development environment. Make sure to provide the correct configuration settings such as database credentials and any other relevant information specific to your deployment or development environment. Also the settings for other chains can be configured there.

### Apply database migrations
```bash
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py migrate --database=userdata
```

### Create a superuser on the user database to be able to access the admin panel
```bash
python3 manage.py createsuperuser --database=userdata
```

### Start the Eth Beaconchain Explorer server. This should only be used in development; for production use e.g. gunicorn+nginx:
```bash
python3 manage.py runserver
```

### Start the Celery worker
To optimize performance, you have the option to specify the concurrency parameter, especially if your machine has limited cores (e.g., `--concurrency=20`). Otherwise, Celery will automatically spawn a process for each available core.
```bash
celery -A ethstakersclub worker --loglevel=info --without-gossip --without-mingle --max-tasks-per-child=80
```

### Start the block listener. This command will start the initial sync.

The synchronization process comprises several stages:

- Initialization: In this phase, all epochs are established, and slots with incomplete data (e.g., proposer) are created. This initialization process is expected to be completed within a day.
- Deposit Retrieval: Subsequently, the system retrieves all deposits from the execution client. This step is anticipated to be finished within an hour.
- Slot Processing: Lastly, each slot is processed, involving the setup of various components such as balance snapshots and other relevant operations. The completion of this stage is estimated to require more than three days.

```bash
python3 manage.py block_listener
```

Congratulations! You have successfully set up the Explorer on your local machine. You can now access the explorer by opening your web browser and visiting http://localhost:8000.
