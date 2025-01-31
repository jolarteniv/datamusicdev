import boto3
import os
import time
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Configura el cliente SQS
sqs = boto3.client('sqs', region_name='us-east-1')  # Cambia la región si es necesario
queue_url = '${queue_url}'  # Parametrizar

output_dir = '${efs_mount_point}'
output_file = os.path.join(output_dir, 'event_log.txt')
lock_file = os.path.join(output_dir, 'lock')

def get_host_info():
    """Obtiene el nombre del host y su dirección IP."""
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return hostname, ip_address

def process_message(message, hostname, ip_address):
    """Procesa un mensaje individual de SQS."""
    receipt_handle = message['ReceiptHandle']
    file_link = message['Body']  # Asumiendo que el cuerpo del mensaje contiene el enlace del archivo

    # Verificar que no haya otro proceso escribiendo en el archivo
    while os.path.exists(lock_file):
        time.sleep(2)

    # Crear archivo de bloqueo para evitar que otros procesos escriban en el archivo
    with open(lock_file, 'w') as f:
        f.write('')

    # Agrega un mensaje al archivo
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_entry = (
        f"[{timestamp}] Archivo nuevo en S3: {file_link}\n"
        f"Evento procesado por: {hostname} (ip: {ip_address})\n\n"
    )
    with open(output_file, 'a') as f:
        f.write(new_entry)

    # Elimina el archivo de bloqueo
    os.remove(lock_file)

    # Genera carga de estrés
    stress_test(${sleep_processing_time})

    # Elimina el mensaje de la cola
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )

def stress_test(duration):
    """Genera carga de estrés en la CPU y la memoria durante un periodo dado."""
    end_time = time.time() + duration
    while time.time() < end_time:
        # Operaciones que consumen CPU
        _ = [x ** 2 for x in range(10000)]
        # Asignación de memoria
        _ = ' ' * (10**6)  # Asigna 1 MB de memoria

def process_sqs_messages():
    """Recibe y procesa mensajes de SQS usando múltiples hilos."""
    hostname, ip_address = get_host_info()  # Obtener información del host

    # Crear un pool de hilos
    with ThreadPoolExecutor(max_workers=${listener_threads}) as executor:
        while True:
            # Recibe mensajes de la cola SQS
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10  # Long Polling
            )

            # Si hay mensajes, procesarlos
            if 'Messages' in response:
                # Enviar cada mensaje al pool de hilos para ser procesado
                for message in response['Messages']:
                    executor.submit(process_message, message, hostname, ip_address)

            time.sleep(${listener_sleep_time})  # Espera antes de volver a verificar

if __name__ == "__main__":
    process_sqs_messages()