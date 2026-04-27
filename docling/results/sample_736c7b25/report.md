# Rapport RAG multi-formats (Docling)

Source d'entree: /home/n7student/Bureau/IA/Parsing/docling/sample.docx
Date: 2026-04-27 22:35:54

## Parametres

- Execution en dur: aucune option CLI necessaire
- Fichier source fixe: /home/n7student/Bureau/IA/Parsing/docling/sample.docx
- Repetitions par methode: 1
- OCR: desactive explicitement pour les images
- Fenetre de contexte image: +/- 250 caracteres
- Envoi LLM: desactive (simulation seulement)

## Resume global

- Total elements traites: 1
- Succes: 1
- Echecs: 0
- Images detectees: 1

## Benchmark Temps (multi-runs)

| Methode | Run 1 (s) | Run 2 (s) | Moyenne (s) | Meilleur parse (s) |
|---|---:|---:|---:|---:|
| Docling (Universal/Auto) | 0.02 | - | 0.02 | 0.02 |

## Tableau des resultats

| Source | Methode | Temps Docling parse (s) | Mots | Tables | Formules bloc | Images | Statut |
|---|---|---:|---:|---:|---:|---:|---|
| /home/n7student/Bureau/IA/Parsing/docling/sample.docx | docling_generic | 0.02 | 20 | 0 | 0 | 1 | OK |

## Element 1: /home/n7student/Bureau/IA/Parsing/docling/sample.docx

- Type: file
- Methode: docling_generic
- Temps Docling parse pur: 0.02s
- Warnings:
  - benchmark_run:1/1

### Metriques

```json
{
  "chars": 484,
  "words": 20,
  "math_inline": 0,
  "math_block": 0,
  "tables_count": 0,
  "images_refs": 1
}
```

### Images

Placeholders images Docling detectes: 1
(Les images reelles sont extraites et affichees dans le fichier `_extracted.md`)

### Contenu extrait (rendu)

---

# Testing DOCX Parsing

This is a test paragraph for DOCX parsing.

![Image](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAIAAAD/gAIDAAAA5klEQVR4nO3QQQkAIADAQLV/Z63gXiLcJRibe3BrvQ74iVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWYFZgVmBWcEBil4Bx/GEGnoAAAAASUVORK5CYII=)

---
