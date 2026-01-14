"""
Script pour convertir README.md en HTML (puis PDF via navigateur)
Version sans dépendances externes
"""

from pathlib import Path
import re
import webbrowser

def markdown_to_html_simple(text):
    """Convertit le markdown en HTML basique"""
    # Échapper les caractères HTML
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Convertir les headers
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Convertir le gras
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    
    # Convertir les listes
    text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    
    # Convertir les blocs de code
    text = re.sub(r'```[a-z]*\n(.*?)\n```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)
    
    # Convertir le code inline
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Convertir les liens
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Convertir les paragraphes
    lines = text.split('\n')
    result = []
    in_list = False
    
    for line in lines:
        if line.strip().startswith('<li>'):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(line)
        else:
            if in_list and not line.strip().startswith('<li>'):
                result.append('</ul>')
                in_list = False
            if line.strip() and not line.strip().startswith('<'):
                result.append(f'<p>{line}</p>')
            else:
                result.append(line)
    
    if in_list:
        result.append('</ul>')
    
    return '\n'.join(result)

def convert_readme_to_html():
    """Convertit le README en HTML avec style"""
    
    # Lire le README
    readme_path = Path("README.md")
    if not readme_path.exists():
        readme_path = Path("Readme.md")
    
    if not readme_path.exists():
        print("❌ Fichier README.md introuvable")
        return
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Convertir en HTML
    html_content = markdown_to_html_simple(content)
    
    # Template HTML avec CSS
    html_template = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edu-ECG - Documentation</title>
    <style>
        @media print {{
            body {{
                margin: 0;
                padding: 20px;
            }}
            .no-print {{
                display: none;
            }}
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        
        .container {{
            background: white;
            padding: 60px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #FF4B4B;
            font-size: 2.5em;
            margin-bottom: 0.5em;
            padding-bottom: 0.3em;
            border-bottom: 3px solid #FF4B4B;
        }}
        
        h2 {{
            color: #1f2937;
            font-size: 1.8em;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
        }}
        
        h3 {{
            color: #374151;
            font-size: 1.3em;
            margin-top: 1.2em;
            margin-bottom: 0.6em;
        }}
        
        p {{
            margin-bottom: 1em;
        }}
        
        strong {{
            color: #1f2937;
        }}
        
        code {{
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
        }}
        
        pre {{
            background: #1f2937;
            color: #e5e7eb;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1em 0;
        }}
        
        pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        
        ul {{
            margin-bottom: 1em;
            padding-left: 30px;
        }}
        
        li {{
            margin-bottom: 0.5em;
        }}
        
        a {{
            color: #FF4B4B;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .print-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #FF4B4B;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        
        .print-button:hover {{
            background: #ff3333;
        }}
        
        @media screen and (max-width: 768px) {{
            .container {{
                padding: 30px;
            }}
            h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-button no-print" onclick="window.print()">📄 Imprimer en PDF</button>
    <div class="container">
        {html_content}
    </div>
    <script>
        // Instructions pour l'utilisateur
        console.log("Pour sauvegarder en PDF :");
        console.log("1. Cliquez sur 'Imprimer en PDF'");
        console.log("2. Dans la fenêtre d'impression, choisissez 'Enregistrer en PDF'");
        console.log("3. Sauvegardez le fichier");
    </script>
</body>
</html>
"""
    
    # Sauvegarder le HTML
    html_filename = "README.html"
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("✅ Fichier HTML généré : README.html")
    print("\n📄 Pour créer le PDF :")
    print("1. Le fichier va s'ouvrir dans votre navigateur")
    print("2. Cliquez sur le bouton 'Imprimer en PDF' en haut à droite")
    print("3. Dans la fenêtre d'impression, choisissez 'Enregistrer en PDF'")
    print("4. Sauvegardez le fichier")
    
    # Ouvrir automatiquement dans le navigateur
    webbrowser.open(html_filename)

if __name__ == "__main__":
    convert_readme_to_html()
