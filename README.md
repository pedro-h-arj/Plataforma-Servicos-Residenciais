# Plataforma de Serviços Residenciais

Sistema web desenvolvido como parte da disciplina de Projeto Aplicado do curso de Análise e Desenvolvimento de Sistemas.

## Objetivo

Facilitar a conexão entre clientes que procuram serviços residenciais e profissionais que oferecem esses serviços.

## Funcionalidades

- Cadastro e login de usuários.
- Perfis de cliente, prestador e administrador.
- Cadastro, edição e exclusão de serviços.
- Pesquisa de serviços disponíveis.
- Edição de dados do perfil.
- Painel administrativo para consulta de usuários.
- Controle de acesso conforme o perfil do usuário.

## Tecnologias utilizadas

- Python
- Flask
- MySQL
- HTML e CSS
- Bootstrap

## Como executar

1. Instale o Python e o MySQL.
2. Configure o banco de dados e as variáveis de ambiente conforme o arquivo `.env.example`.
3. Crie e ative o ambiente virtual:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

4. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

5. Entre na pasta `backend` e execute:

   ```bash
   python app.py
   ```

6. Acesse no navegador o endereço apresentado no terminal, geralmente `http://127.0.0.1:5000`.

## Banco de dados

O sistema utiliza o MySQL, com tabelas para armazenar os usuários e os serviços cadastrados.

## Segurança

As senhas são armazenadas por meio de hash, e as credenciais do banco de dados devem ser mantidas no arquivo `.env`, que não deve ser enviado ao GitHub.
