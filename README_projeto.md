# Projeto de Automação com Agente de IA

## Visão Geral
Este projeto implementa um pipeline completo de automação para leitura de listas de exames digitalizadas e preenchimento automático de relatório institucional.

A solução combina visão computacional, IA multimodal e processamento de dados para transformar documentos não estruturados em dados confiáveis.

## Problema
As listas apresentam:
- Estrutura inconsistente
- Dados manuscritos
- Baixa qualidade de imagem

OCR tradicional não resolve o problema.

## Solução
Pipeline com IA multimodal (Gemini):

Imagens → Pré-processamento → IA → JSON → CSV → Excel

## Tecnologias
- Python
- OpenCV
- Pandas
- OpenPyXL
- Google Gemini

## Arquitetura
Sistema dividido em:
- Entrada
- Processamento
- Resultados
- Sistema
- Aprendizado

## Diferenciais
- Pipeline auditável
- Controle de custo de IA
- Persistência incremental
- Integração com Excel institucional

## Status
Sistema funcional em produção interna.

## Próximos passos
- Interface gráfica
- Dashboard
- Validação automática avançada
