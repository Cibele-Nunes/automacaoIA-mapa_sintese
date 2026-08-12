# 🧠 Projeto de Automação com IA Multimodal
### Leitura de Listas de Exames e Preenchimento Automático de Relatório Institucional

![status](https://img.shields.io/badge/status-em%20uso%20real-success)
![python](https://img.shields.io/badge/python-3.10+-blue)
![ia](https://img.shields.io/badge/IA-multimodal-purple)

---

## 📌 Visão Geral

Este projeto implementa um pipeline completo de automação documental utilizando Inteligência Artificial multimodal para interpretar listas de exames digitalizadas e transformar esses dados em relatórios institucionais oficiais.

A solução resolve um problema real de operação administrativa escolar, conectando documentos físicos a sistemas digitais de forma automatizada, auditável e escalável.

---

## ⚠️ Problema

As listas de exames apresentam desafios significativos:

- Estrutura inconsistente (tabelas reiniciando)
- Presença de dados manuscritos
- Baixa qualidade de digitalização
- Cabeçalhos repetidos e ruído visual

Esses fatores tornam soluções tradicionais de OCR insuficientes, pois o problema exige **interpretação contextual**, não apenas leitura de texto.

---

## 💡 Solução

O sistema utiliza um pipeline baseado em IA multimodal:

```
IMAGENS
  ↓
Pré-processamento (OpenCV)
  ↓
IA Multimodal (Gemini)
  ↓
JSON estruturado
  ↓
Validação
  ↓
CSV auditável
  ↓
Agregação estatística
  ↓
Excel institucional
```

A IA interpreta as imagens de forma semelhante à leitura humana, permitindo lidar com inconsistências estruturais.

---

## 🏗️ Arquitetura

O sistema é organizado em camadas:

- **Entrada:** imagens brutas no Google Drive  
- **Processamento:** pré-processamento + extração + validação  
- **Resultados:** CSVs, logs e relatório final  
- **Sistema:** modelo Excel, prompts e configuração  
- **Aprendizado:** base para melhorias futuras  

---

## 🔍 Diferenciais Técnicos

- Uso de **IA multimodal** em problema real  
- Pipeline **auditável ponta a ponta**  
- Controle de custo via **cache de JSON**  
- Persistência incremental do Excel anual  
- Tratamento de dados com validação automática  
- Integração com planilha institucional complexa  

---

## 📊 Tecnologias Utilizadas

- Python  
- OpenCV  
- Pandas  
- OpenPyXL  
- Google Gemini API  
- Google Colab  

---

## 📈 Impacto

Antes:
- Processo manual, lento e sujeito a erro  

Depois:
- Automação completa do fluxo  
- Redução de esforço operacional  
- Aumento de confiabilidade dos dados  
- Padronização do processo  

---

## 🚀 Como Executar (Resumo)

1. Definir ANO e MÊS no notebook  
2. Inserir imagens no Drive  
3. Executar pipeline  
4. Revisar CSV gerado  
5. Validar e gerar relatório Excel  

---

## 🔮 Próximos Passos

- Interface gráfica para usuários  
- Dashboard de indicadores  
- Validação automática IA × dados  
- Aprimoramento de leitura manuscrita  

---

## 👨‍💻 Autor

Projeto desenvolvido como solução real de automação administrativa com foco em engenharia de dados e IA aplicada.

---

## ⭐ Destaque para Portfólio

Este projeto demonstra:

- Engenharia de pipelines de dados  
- Aplicação prática de IA generativa  
- Integração entre visão computacional e dados  
- Construção de sistemas reais e utilizáveis  

