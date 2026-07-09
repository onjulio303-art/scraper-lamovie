import os
import asyncio
from fastapi import FastAPI
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

app = FastAPI(title="LaMovie API")

# Comando especial para que Render instale el navegador automáticamente
os.system("playwright install chromium")
os.system("playwright install-deps")

@app.get("/")
def inicio():
    return {"mensaje": "API activa. Visita /peliculas para ver la lista maestra."}

@app.get("/peliculas")
async def obtener_peliculas():
    url_objetivo = "https://lamovie.org"
    peliculas = []
    enlaces_unicos = set()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = await context.new_page()
        
        try:
            await page.goto(url_objetivo, wait_until="networkidle", timeout=60000)
            html_final = await page.content()
            soup = BeautifulSoup(html_final, 'html.parser')
            
            for item in soup.find_all('a', href=True):
                enlace = item['href']
                
                if "/peliculas/" in enlace and enlace != "https://lamovie.org" and "/page/" not in enlace:
                    if enlace not in enlaces_unicos:
                        titulo = item.text.strip()
                        imagen = item.find('img')
                        
                        if imagen and imagen.get('alt'):
                            titulo = imagen['alt'].strip()
                        elif not titulo and item.get('title'):
                            titulo = item['title'].strip()
                            
                        if not titulo or len(titulo) < 2:
                            titulo = enlace.split('/')[-2].replace('-', ' ').title()
                        
                        peliculas.append({
                            "titulo": titulo,
                            "enlace": enlace
                        })
                        enlaces_unicos.add(enlace)
                        
        except Exception as e:
            return {"error": f"Fallo al conectar: {str(e)}"}
        finally:
            await browser.close()
            
    return {"total_peliculas": len(peliculas), "peliculas": peliculas}
