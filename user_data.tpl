#! /bin/bash

# Configure working dir
WORKING_DIR=/app/datamusic
# Remove the working directory if it exists
sudo rm -rf $WORKING_DIR
# Create the working directory
sudo mkdir -p $WORKING_DIR
cd $WORKING_DIR

# Redirect all output to a log file
exec > $WORKING_DIR/provision.log 2>&1

# Mount EFS and install libraries
echo "[PROVISIONING] Instalando librerías..."
sudo apt update -y && sudo apt install -y nfs-common python3.12 python3-pip python3-full unzip git
sudo sudo snap install aws-cli --classic
echo "[PROVISIONING] Montando EFS..."
sudo mkdir -p ${efs_mount_point}
sudo mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport ${efs_host}:/ ${efs_mount_point}

# Configurar credenciales de AWS
export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"
export AWS_DEFAULT_REGION="us-east-1"

# Set ~/.aws/credentials with the provided credentials
sudo mkdir -p ~/.aws
sudo cat << EOF > ~/.aws/credentials
[default]
aws_access_key_id = $AWS_ACCESS_KEY_ID
aws_secret_access_key = $AWS_SECRET_ACCESS_KEY
EOF

#clone repo
git clone git@github.com:jolarteniv/datamusicdev.git $WORKING_DIR

# Create python virtual environment
echo "[PROVISIONING] Creando entorno virtual de Python..."
sudo mkdir -p $WORKING_DIR/venv
sudo python3 -m venv $WORKING_DIR/venv
sudo bash -c "source $WORKING_DIR/venv/bin/activate && echo '[PROVISIONING] Entorno virtual activado'"

# Install requirements (if not exists, show a message only)
echo "[PROVISIONING] Instalando librerías de Python..."

sudo $WORKING_DIR/venv/bin/pip3 install -r $WORKING_DIR/requirements.txt || echo "[PROVISIONING] No se encontró el archivo requirements.txt"
sudo $WORKING_DIR/venv/bin/pip3 install Flask boto3

# Correr archivos de Python
echo "[PROVISIONING] Corriendo archivos de Python..."

# Correr listener en segundo plano
echo "[PROVISIONING] Corriendo listener de SQS..."
sudo $WORKING_DIR/venv/bin/python3 $WORKING_DIR/src/track_recognizer_consumer.py &

# Correr aplicación Flask
echo "[PROVISIONING] Corriendo aplicación Flask..."
sudo $WORKING_DIR/venv/bin/python3 $WORKING_DIR/app.py
