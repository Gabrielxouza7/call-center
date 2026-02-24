# Call Center System

Este projeto consiste em um sistema de gerenciamento de Call Center. A solução utiliza o framework Twisted para implementar uma arquitetura orientada a eventos, garantindo que o sistema seja assíncrono e não-bloqueante.

## Tecnologias e Conceitos
* **Python 3**: Linguagem principal para a lógica de servidor e cliente.
* **Twisted**: Gerenciamento de múltiplas conexões e eventos de tempo (timeouts) em uma única thread.
* **Docker & Docker Compose**: Containerização completa utilizando **Rocky Linux** como base, garantindo portabilidade e conformidade com requisitos de sistemas Red Hat.
* **JSON**: Protocolo de serialização para comunicação estruturada entre os componentes.



## Arquitetura do Sistema

O sistema é dividido em dois serviços principais:

1.  **Servidor (`server.py`)**: Atua como o cérebro do sistema, gerenciando uma máquina de estados para os operadores. Ele controla quem está available, ringing ou busy, além de gerenciar a fila de chamadas pendentes e disparar notificações automáticas após 10 segundos de inatividade.
2.  **Cliente (`client.py`)**: Interface de terminal que utiliza multiplexação de I/O. Com o stdio.StandardIO, o cliente consegue processar a digitação do usuário e receber atualizações em tempo real do servidor simultaneamente.



## Como Executar

As imagens deste projeto estão hospedadas no Docker Hub, então basta ter o Docker instalado.

### 1. Criar o arquivo de orquestração
Crie um arquivo chamado `docker-compose.yml` e cole o conteúdo abaixo:

```yaml
services:
  server:
    image: gabrielssouza2702/call-center-server:v1.0
    container_name: call-server
    ports:
      - "5678:5678"

  client:
    image: gabrielssouza2702/call-center-client:v1.0
    container_name: call-client
    stdin_open: true
    tty: true
    depends_on:
      - server
```
### 2. Iniciar os serviços

No terminal, dentro da pasta onde o arquivo foi criado, execute:
```
sudo docker-compose up -d
```
### 3. Interagir com o Cliente

Para acessar o terminal interativo do cliente e começar a enviar comandos:
```
docker attach call-client
```
