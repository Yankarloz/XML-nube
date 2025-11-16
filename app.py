from spyne import Application, rpc, ServiceBase, Unicode, Integer
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from lxml import etree

XML_FILE = "xml/datos.xml"

def cargar_xml():
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(XML_FILE, parser)


def guardar_xml(tree):
    tree.write(
        XML_FILE,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    )




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


class CRUDService(ServiceBase):

    @rpc(_returns=Unicode)
    def listar(ctx):
        tree = cargar_xml()
        return etree.tostring(tree.getroot(), pretty_print=True, encoding="unicode")

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

        nuevo = etree.SubElement(root, "producto")
        nuevo.set("id", str(nuevo_id))
        etree.SubElement(nuevo, "nombre").text = nombre
        etree.SubElement(nuevo, "precio").text = precio
        etree.SubElement(nuevo, "cantidad").text = cantidad

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

    # -------------------------------------------------
    # 🔥 AHORA SÍ — MÉTODO ACTUALIZAR DENTRO DE LA CLASE
    # -------------------------------------------------
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

    # -------------------------------------------------
    # 🔥 MÉTODO REPORTE DENTRO DE LA CLASE
    # -------------------------------------------------
    @rpc(_returns=Unicode)
    def reporte(ctx):
        tree = cargar_xml()
        root = tree.getroot()

        total_productos = len(root.findall("producto"))
        total_precios = sum(float(p.find("precio").text) for p in root.findall("producto"))

        reporte = etree.Element("reporte")
        etree.SubElement(reporte, "total_productos").text = str(total_productos)
        etree.SubElement(reporte, "suma_total_precios").text = str(total_precios)

        porcentajes = etree.SubElement(reporte, "porcentajes")

        for p in root.findall("producto"):
            precio = float(p.find("precio").text)
            porc = (precio / total_precios) * 100 if total_precios else 0

            nodo = etree.SubElement(porcentajes, "producto")
            nodo.set("id", p.get("id"))
            etree.SubElement(nodo, "nombre").text = p.find("nombre").text
            etree.SubElement(nodo, "precio").text = str(precio)
            etree.SubElement(nodo, "porcentaje").text = f"{porc:.2f}"

        return etree.tostring(reporte, pretty_print=True, encoding="unicode")


# -------------------------------------------------
# WSGI
# -------------------------------------------------
application = Application(
    [CRUDService],
    "mi.soap.crud",
    in_protocol=Soap11(),
    out_protocol=Soap11()
)

app = CORSWrapper(WsgiApplication(application))


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    print("Servidor SOAP en http://127.0.0.1:8000/?wsdl")
    server = make_server("0.0.0.0", 8000, app)
    server.serve_forever()

