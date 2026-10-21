---
issue: "Identificação e desenho de pessoas fora da zona ROI"
date: "2026-10-16"
status: resolved
approach: "Filtragem estrita no overlay — caixas e IDs desenhados exclusivamente para pessoas dentro do ROI ativo"
verification: "Novo teste unitário test_desenha_caixas_filtra_fora_do_roi passando; 33/33 testes verdes"
---

# PLANO DE AÇÃO & RESOLUÇÃO — Filtragem Visual Estrita por ROI

## 1. Objetivo
Garantir que pessoas fora da zona demarcada (ROI) não tenham caixas delimitadoras (`bounding boxes`), IDs nem métricas desenhadas na tela, tornando a visualização 100% fiel à delimitação da zona.

## 2. Alterações Realizadas
1. **`overlay.py` (`desenhar_caixas`):**
   - Atualizado para aceitar o parâmetro opcional `zonas`.
   - Se `zonas` for fornecido, testa se a base do pé da pessoa (`pe_x, pe_y`) está dentro de algum ROI ativo usando `cv2.pointPolygonTest`.
   - Se estiver fora de todos os ROIs, a caixa e o rótulo são ignorados.
2. **`main.py`:**
   - Passa `zonas=zonas` para `overlay.desenhar_caixas(frame, caixas, zonas=zonas)`.
   - O HUD (`Pessoas: N`) agora reflete a ocupação total somada das zonas em vez de todas as pessoas globais do campo da câmera.
3. **`tests/test_overlay.py`:**
   - Adicionado teste `test_desenha_caixas_filtra_fora_do_roi`, garantindo que pessoas fora do polígono não geram alterações de pixel no frame e pessoas dentro geram.
4. **Verificação:**
   - Suíte completa rodou com **33/33 testes passando**.

