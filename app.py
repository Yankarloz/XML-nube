from spyne import Application, rpc, ServiceBase, Unicode, Integer
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import os

# ==========================================================
#   RUTA CORRECTA DEL XML (FUNCIONA EN WINDOWS Y RENDER)
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
XML_FILE = os.path.join(BASE_DIR, "xml", "datos.xml")
FRONT_DIR = os.path.join(BASE_DIR, "front")

def cargar_xml():
    return ET.parse(XML_FILE)


def guardar_xml(tree):
    # Use ElementTree.indent to produce consistent pretty XML without
    # the extra blank lines/minidom artifacts. Write with XML declaration.
    try:
        ET.indent(tree, space="\t")
    except Exception:
        # fallback: no-op if indent not available
        pass
    tree.write(XML_FILE, encoding="utf-8", xml_declaration=True)


def _safe_float(value):
    try:
        if value is None:
            return 0.0
        # strip if it's a string
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return 0.0
        return float(value)
    except Exception:
        return 0.0

# ==========================================================
#   CORS
# ==========================================================

class CORSWrapper(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def cors_start_response(status, headers, exc_info=None):
            headers.append(("Access-Control-Allow-Origin", "*"))
            headers.append(("Access-Control-Allow-Methods", "GET, POST, OPTIONS"))
            headers.append(("Access-Control-Allow-Headers", "Content-Type"))
            return start_response(status, headers, exc_info)

        if environ["REQUEST_METHOD"] == "OPTIONS":
            start_response("200 OK", [
                ("Content-Type", "text/plain"),
                ("Access-Control-Allow-Origin", "*"),
                ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                ("Access-Control-Allow-Headers", "Content-Type"),
            ])
            return [b""]

        return self.app(environ, cors_start_response)


# ==========================================================
#   SERVICIO SOAP
# ==========================================================

class CRUDService(ServiceBase):

    @rpc(_returns=Unicode)
    def listar(ctx):
        tree = cargar_xml()
        # indent the tree for a consistent readable output
        try:
            ET.indent(tree, space="\t")
        except Exception:
            pass
        return ET.tostring(tree.getroot(), encoding="unicode")


    @rpc(Unicode, Unicode, Unicode, _returns=Unicode)
    def agregar(ctx, nombre, precio, cantidad):
        tree = cargar_xml()
        root = tree.getroot()

        ids = []
        for p in root.findall("producto"):
            try:
                ids.append(int(p.get("id")))
            except:
                pass

        nuevo_id = max(ids) + 1 if ids else 1

        nuevo = ET.SubElement(root, "producto")
        nuevo.set("id", str(nuevo_id))
        ET.SubElement(nuevo, "nombre").text = nombre
        ET.SubElement(nuevo, "precio").text = precio
        ET.SubElement(nuevo, "cantidad").text = cantidad

        guardar_xml(tree)
        return "Producto agregado"

    @rpc(Integer, _returns=Unicode)
    def eliminar(ctx, producto_id):
        tree = cargar_xml()
        root = tree.getroot()

        for prod in root.findall("producto"):
            if prod.get("id") == str(producto_id):
                root.remove(prod)
                guardar_xml(tree)
                return f"Producto {producto_id} eliminado"

        return "ID no encontrado"

    @rpc(Integer, Unicode, Unicode, Unicode, _returns=Unicode)
    def actualizar(ctx, producto_id, nombre, precio, cantidad):
        tree = cargar_xml()
        root = tree.getroot()

        for prod in root.findall("producto"):
            if prod.get("id") == str(producto_id):

                if nombre.strip() != "":
                    prod.find("nombre").text = nombre

                if precio.strip() != "":
                    prod.find("precio").text = precio

                if cantidad.strip() != "":
                    prod.find("cantidad").text = cantidad

                guardar_xml(tree)
                return f"Producto {producto_id} actualizado"

        return "ID no encontrado"

    @rpc(_returns=Unicode)
    def reporte(ctx):
        tree = cargar_xml()
        root = tree.getroot()

        total_productos = len(root.findall("producto"))
        total_precios = sum(_safe_float(p.find("precio").text if p.find("precio") is not None else None) for p in root.findall("producto"))

        reporte = ET.Element("reporte")
        ET.SubElement(reporte, "total_productos").text = str(total_productos)
        ET.SubElement(reporte, "suma_total_precios").text = str(total_precios)

        porcentajes = ET.SubElement(reporte, "porcentajes")

        for p in root.findall("producto"):
            precio = _safe_float(p.find("precio").text if p.find("precio") is not None else None)
            porc = (precio / total_precios) * 100 if total_precios else 0

            nodo = ET.SubElement(porcentajes, "producto")
            nodo.set("id", p.get("id"))
            nombre_node = p.find("nombre")
            nombre_text = nombre_node.text if (nombre_node is not None and nombre_node.text) else "(sin nombre)"
            ET.SubElement(nodo, "nombre").text = nombre_text
            ET.SubElement(nodo, "precio").text = str(precio)
            ET.SubElement(nodo, "porcentaje").text = f"{porc:.2f}"

        try:
            ET.indent(reporte, space="\t")
        except Exception:
            pass
        return ET.tostring(reporte, encoding="unicode")


# ==========================================================
#   WSGI + FRONTEND
# ==========================================================

# -------------------------------------------------
# SOAP Application
# -------------------------------------------------
application = Application(
    [CRUDService],
    "mi.soap.crud",
    in_protocol=Soap11(),
    out_protocol=Soap11()
)


from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask import Flask, send_from_directory


front = Flask(__name__, static_folder=FRONT_DIR, template_folder=FRONT_DIR)

@front.route("/")
def home():
    return send_from_directory(FRONT_DIR, "index.html")

@front.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(FRONT_DIR, path)


soap_app = CORSWrapper(WsgiApplication(application))

# Serve FRONTEND at / and SOAP under /soap
app = DispatcherMiddleware(front, {
    "/soap": soap_app
})

if __name__ == "__main__":
    print("🚀 Servidor iniciado")
    port = int(os.environ.get("PORT", 8000))
    print(f"SOAP WSDL → http://127.0.0.1:{port}/soap?wsdl")
    print(f"FRONTEND → http://127.0.0.1:{port}/")
    
    run_simple("0.0.0.0", port, app, use_reloader=True)
