/* app.js - todo el comportamiento JS del frontend */

/* ENDPOINT del servicio SOAP */
const SOAP_URL = "http://127.0.0.1:8000";

/* helpers */
async function enviarSOAP(xmlBody) {
  const res = await fetch(SOAP_URL, {
    method: "POST",
    headers: { "Content-Type": "text/xml" },
    body: `
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                      xmlns:ser="mi.soap.crud">
       <soapenv:Body>
          ${xmlBody}
       </soapenv:Body>
    </soapenv:Envelope>`
  });
  return await res.text();
}

function desescaparXML(txt) {
  return txt
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
}

function formatearXML(xmlString) {
  try {
    return vkbeautify.xml(xmlString);
  } catch (e) {
    return xmlString;
  }
}

/* parseo seguro compatible con namespaces */
function extraerResultadoPorTag(respuestaText, tag) {
  // captura <ns:tag ...>...</ns:tag>
  const regex = new RegExp(`<[^:>]*:${tag}[^>]*>([\\s\\S]*?)<\\/[^^:>]*:${tag}>`);
  const m = respuestaText.match(regex);
  if (m) return m[1];
  // fallback sin namespace
  const regex2 = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`);
  const m2 = respuestaText.match(regex2);
  return m2 ? m2[1] : null;
}

/* DOM helpers */
function $id(id){ return document.getElementById(id); }

/* Handlers principales */
async function onAgregar(e) {
  e.preventDefault();
  const f = new FormData(e.target);
  const body = `<ser:agregar>
                  <ser:nombre>${f.get("nombre")}</ser:nombre>
                  <ser:precio>${f.get("precio")}</ser:precio>
                  <ser:cantidad>${f.get("cantidad")}</ser:cantidad>
                </ser:agregar>`;
  const res = await enviarSOAP(body);
  alert("Respuesta:\n" + res);
}

async function onActualizar(e) {
  e.preventDefault();
  const f = new FormData(e.target);
  const body = `<ser:actualizar>
                  <ser:producto_id>${f.get("id")}</ser:producto_id>
                  <ser:nombre>${f.get("nombre")}</ser:nombre>
                  <ser:precio>${f.get("precio")}</ser:precio>
                  <ser:cantidad>${f.get("cantidad")}</ser:cantidad>
                </ser:actualizar>`;
  const res = await enviarSOAP(body);
  alert("Respuesta:\n" + res);
}

async function onEliminar(e) {
  e.preventDefault();
  const f = new FormData(e.target);
  const body = `<ser:eliminar>
                  <ser:producto_id>${f.get("id")}</ser:producto_id>
                </ser:eliminar>`;
  const res = await enviarSOAP(body);
  alert("Respuesta:\n" + res);
}

async function onListar() {
  const res = await enviarSOAP(`<ser:listar/>`);
  const contenido = extraerResultadoPorTag(res, "listarResult");
  $id("xmlArea").value = contenido ? formatearXML(desescaparXML(contenido)) : "No se pudo procesar la respuesta de listar.";
}

async function onReporte() {
  const res = await enviarSOAP(`<ser:reporte/>`);
  const contenido = extraerResultadoPorTag(res, "reporteResult");
  if (!contenido) {
    $id("xmlArea").value = "No se pudo procesar el reporte.";
    return;
  }

  const xmlStr = desescaparXML(contenido);
  $id("xmlArea").value = formatearXML(xmlStr);

  // parsear y mostrar resumen visual
  const parser = new DOMParser();
  const xml = parser.parseFromString(xmlStr, "application/xml");

  const totalProductosEl = xml.getElementsByTagName("total_productos")[0];
  const sumaPreciosEl = xml.getElementsByTagName("suma_total_precios")[0];

  $id("totalProductos").textContent = totalProductosEl ? totalProductosEl.textContent : "0";
  $id("sumaPrecios").textContent = sumaPreciosEl ? "$" + sumaPreciosEl.textContent : "$0";

  const productos = xml.getElementsByTagName("producto");
  let listaHTML = "";
  for (let p of productos) {
    const nombreEl = p.getElementsByTagName("nombre")[0];
    const porcentajeEl = p.getElementsByTagName("porcentaje")[0];
    const nombre = nombreEl ? nombreEl.textContent : "(sin nombre)";
    const porcentaje = porcentajeEl ? porcentajeEl.textContent : "0.00";
    listaHTML += `<li><strong>${escapeHtml(nombre)}</strong> → ${escapeHtml(porcentaje)}%</li>`;
  }
  $id("listaPorcentajes").innerHTML = listaHTML;
  $id("reporteVisual").style.display = "block";
}

/* pequeña función para escapar texto mostrado en HTML */
function escapeHtml(s) {
  return String(s)
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;");
}

/* Inicializador */
function init() {
  $id("agregarForm").addEventListener("submit", onAgregar);
  $id("actualizarForm").addEventListener("submit", onActualizar);
  $id("eliminarForm").addEventListener("submit", onEliminar);
  $id("btnListar").addEventListener("click", onListar);
  $id("btnReporte").addEventListener("click", onReporte);
}

/* arrancar cuando DOM esté listo */
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
