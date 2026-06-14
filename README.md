# MOCP - My Own C in Português

**UAb 2025/2026 – Unidade Curricular de Compilação**  

<img width="420" height="420" alt="logo" src="https://github.com/user-attachments/assets/dc6dc0f6-ef6b-4fa8-8a2e-ee60c5c5f3d6" />


Este projeto implementa um compilador completo para a linguagem  **MOCP (My Own C in Project)**, uma linguagem fictícia inspirada em C com palavras-chave em português. O compilador cobre todas as fases: análise léxica e sintática, análise semântica, geração de código intermédio (TAC), otimização desse código e geração de código final P3 Assembly.

---

## 📘 Introdução

A linguagem **MOCP** foi concebida para facilitar o estudo e a experimentação de conceitos de compilação, utilizando ferramentas como o **ANTLR4**.  

Este repositório inclui:  
- A gramática completa da linguagem em ANTLR4 (`MOCP.g4`)  
- Scripts para compilação, análise e validação de programas escritos em MOCP 
- Gerador de código intermédio TAC com quádruplas estruturadas  
- Otimizador com 6 técnicas: constant folding, propagação de cópias, CSE, LICM, código inatingível e código morto 
- Gerador de código final P3 Assembly para o simulador P3JS, com suporte a recursão

---

## 🛠 Requisitos

- **Python 3.10 ou superior**  
- **ANTLR versão 4.13.2**  
- **Java instalado** (necessário para executar o ANTLR)  
- **Simulador P3JS** (opcional, para executar o assembly gerado): https://p3js.goncalomb.com/

---

## 📂 Estrutura do Projeto

```text
MOCP/
├── MOCP.g4                           # Gramática ANTLR4 da linguagem MOCP (léxico + sintaxe)
├── MOCPErrorListener.py              # Intercepta e traduz erros do ANTLR4 em mensagens amigáveis para MOCP.
├── MOCPErrorMessages                 # Mensagens de erro semântico padronizadas (funções auxiliares)
├── MOCPSemanticAnalyzer              # Analisador semântico: valida tipos, declarações, escopos, protótipos e chamadas
├── MOCPSymbolTable                   # Tabela de símbolos com suporte a escopos aninhados
├── MOCPIntermediateCodeGenerator.py  # Gerador de código intermédio TAC (quádruplas)
├── MOCPCodeOptimiser.py              # Otimizador de TAC (6 técnicas)
├── MOCPCodeGenerator_P3.py           # Gerador de código final P3 Assembly (P3JS)
├── constants.py                      # Mapeamento entre palavras‑chave MOCP e C
├── main.py                           # Script principal para execução e análise
├── utils.py                          # Funções utilitárias
├── Testes_compilador.py              # Testes automáticos (41 testes unittest)
├── Testes/                           # Programas MOCP de teste (.mocp): 6 válidos, 7 de otimização e 15 de rejeição
└── README.md                         # Documentação geral do projeto, instruções de uso e exemplos
```

---
## 🚀 Como Executar

### 1️⃣ Instalar Python

**Windows:**
1. Verifique se o Python 3 está instalado:
```bash
python --version
```
2. Caso não esteja, aceder a https://www.python.org/downloads/windows/ 
3. Clique em “Download Python 3.X”  
4. Durante a instalação, ative **Add Python to PATH**  
5. Verificar a instalação:  
```bash
python --version
```

**Linux/Mac:**
1. Verifique se o Python 3 está instalado:
```bash
python --version
```
2. Caso não esteja, use o gestor de pacotes da sua distribuição
```bash
sudo apt install python3
```
ou
```bash
brew install python3
```

---

## 2️⃣ Terminal:

- Windows: CMD, PowerShell ou Git Bash

- Linux/Mac: terminal nativo


**Como utilizar:**

Compila um programa MOCP e apresenta o TAC gerado e otimizado
```bash
python3 main.py Testes/teste1.mocp
```

Para gerar a árvore textual
```bash
python3 main.py Testes/teste1.mocp -tree
```
Para abrir a GUI da árvore
```bash
python3 main.py Testes/teste1.mocp -gui
```
Para gerar código P3 Assembly em `Output_P3/<nome>.as`, carregável no simulador P3JS
```bash
python3 main.py Testes/teste1.mocp -p3
```
⚠️ As opções `-tree` e `-gui` requerem que o ANTLR4 esteja instalado e que o `antlr4-parse` esteja configurado no PATH do sistema.

⚠️ A opção `-p3` rejeita programas que usem o tipo `real` com uma mensagem clara, dado que o P3 não tem unidade de vírgula flutuante. As restantes fases continuam a funcionar normalmente para esses programas.

---

## 3️⃣ Preparar o ambiente
1. Instale o ANTLR4 e adicione ao PATH (ver instruções em: https://github.com/antlr/antlr4)
2. Instale a runtime Python do ANTLR4:
```bash
pip install antlr4-python3-runtime
```

---

## 4️⃣ Compilar a gramática
```bash
antlr4 -Dlanguage=Python3 -visitor MOCP.g4
```

---

## 5️⃣ Executar os testes automáticos
```bash
python3 Testes_compilador.py
```

---

## 6️⃣ Gerar um executável standalone

Para utilizadores que não queiram instalar Python e ANTLR, o projeto inclui scripts que produzem um executável único.

**Windows:**
```bash
build_exe.bat
```

**Linux/Mac:**
```bash
./build_exe.sh
```

O executável é gerado em `dist/mocp.exe` (Windows) ou `dist/mocp` (Linux/Mac). Pode ser invocado com a mesma sintaxe do `main.py`:
```bash
dist/mocp Testes/teste1.mocp -p3
```

---

## 🧰 Versões do software utilizado

- Python 3.14.3
- ANTLR 4.13.2
- Java 26.0.1 (OpenJDK HotSpot 64-Bit Server VM, build 26.0.1+8-34)
- Simulador P3JS: https://p3js.goncalomb.com/

---

## Autores
- Undefined Behaviour Team 1
  -  Mariana Barrote - 2200640
  -  Rui Correia - 2102862
- Undefined Behaviour Team 2
  -  Joana Regalado - 2300250
  -  Rafael Sousa - 2301433

UC de Compilação - Universidade Aberta, 2025/2026
