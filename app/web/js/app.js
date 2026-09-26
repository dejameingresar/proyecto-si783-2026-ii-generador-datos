/* DataForge — controlador de la interfaz. Sin dependencias ni framework.
 * Toda la logica vive en el servidor (app/nucleo/api.py); aqui solo se pinta. */
'use strict';

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const estado = {
  esquema: null,
  ultimoSql: null,
  nombreDescarga: 'datos.sql',
};

async function pedir(ruta, opciones) {
  const r = await fetch(ruta, opciones);
  return { status: r.status, datos: await r.json() };
}

function avisa(texto, clase = 'ok') {
  const el = $('#estado');
  el.textContent = texto;
  el.className = 'estado ' + clase;
  el.hidden = false;
}

function ocultaAviso() { $('#estado').hidden = true; }

// ------------------------------------------------------------------ esquema
function pintaVolumenes(esc) {
  const cont = $('#volumenes');
  cont.innerHTML = '';
  for (const nombre of esc.orden) {
    const t = esc.tablas[nombre];
    const card = document.createElement('div');
    card.className = 'vol-card';

    const cab = document.createElement('div');
    cab.className = 'nombre';
    cab.textContent = nombre;
    card.appendChild(cab);

    const desc = document.createElement('div');
    desc.className = 'desc';
    desc.textContent = t.descripcion || (t.columnas.length + ' columnas');
    card.appendChild(desc);

    const fks = t.campos.filter((c) => c.tipo === 'fk');
    if (fks.length) {
      const fk = document.createElement('div');
      fk.className = 'fk';
      fk.textContent = 'FK → ' + fks.map((c) => c.tabla_ref).join(', ');
      card.appendChild(fk);
    }

    const fila = document.createElement('div');
    fila.className = 'fila';
    const rango = document.createElement('input');
    rango.type = 'range';
    rango.min = '0';
    rango.max = '600';
    // step=1, no step=10: con un paso de 10 el deslizador no puede representar
    // los volumenes por defecto (especialidad=8, medico=25) y el navegador los
    // redondea en silencio, de modo que la pantalla mostraria un total distinto
    // del que se pidio. Un paso de 1 hace que lo que se ve sea lo que se genera.
    rango.step = '1';
    rango.value = String(t.volumen);
    rango.id = 'vol-' + nombre;
    rango.setAttribute('aria-label', 'filas de ' + nombre);
    const out = document.createElement('output');
    out.textContent = t.volumen;
    rango.addEventListener('input', () => { out.textContent = rango.value; });
    fila.appendChild(rango);
    fila.appendChild(out);
    card.appendChild(fila);

    cont.appendChild(card);
  }
}

function volumenesActuales() {
  const vol = {};
  for (const nombre of (estado.esquema ? estado.esquema.orden : [])) {
    vol[nombre] = parseInt($('#vol-' + nombre).value, 10) || 0;
  }
  return vol;
}

// ------------------------------------------------------------------ métricas
function pct(x) { return (x * 100).toFixed(0) + '%'; }

function pintaMetricas(d) {
  const cont = $('#metricas');
  cont.innerHTML = '';
  const r = d.resumen;

  const pills = document.createElement('div');
  pills.className = 'resumen-fila';
  const unicos = Object.values(d.lote.tablas)
    .reduce((a, t) => a + t.unicos_respetados, 0);
  const unicosTot = Object.values(d.lote.tablas)
    .reduce((a, t) => a + t.unicos_total, 0);
  const huerfanos = Object.values(d.lote.tablas)
    .reduce((a, t) => a + Object.values(t.fk_respetadas)
      .reduce((b, f) => b + f.huerfanos, 0), 0);
  const celdasVacias = d.lote.totales.celdas_vacias;

  const items = [
    ['filas', r.filas_totales, false],
    ['unicidad', unicos + '/' + unicosTot, unicos !== unicosTot],
    ['completitud', pct(r.completitud), r.completitud < 1],
    ['huerfanos', huerfanos, huerfanos > 0],
    ['celdas vacías', celdasVacias, celdasVacias > 0],
    ['tiempo', r.generado_en, false],
  ];
  for (const [k, v, mala] of items) {
    const p = document.createElement('span');
    p.className = 'pastilla' + (mala ? ' rota' : '');
    p.innerHTML = k + ' <b></b>';
    p.querySelector('b').textContent = v;
    pills.appendChild(p);
  }
  cont.appendChild(pills);

  const tabla = document.createElement('table');
  tabla.innerHTML =
    '<thead><tr><th>tabla</th><th class="num">filas</th><th class="num">cols</th>' +
    '<th>unicidad</th><th>completitud</th><th>dominios enum</th><th>integridad FK</th></tr></thead>';
  const tbody = document.createElement('tbody');

  for (const nombre of estado.esquema.orden) {
    const t = d.lote.tablas[nombre];
    if (!t) continue;
    const tr = document.createElement('tr');

    const tdN = document.createElement('td');
    tdN.innerHTML = '<code></code>';
    tdN.querySelector('code').textContent = nombre;
    tr.appendChild(tdN);

    tr.appendChild(celdaNum(t.filas));
    tr.appendChild(celdaNum(t.columnas));
    tr.appendChild(celdaSiNo(t.unicos_respetados === t.unicos_total && t.pk_unica,
      t.unicos_total ? t.unicos_respetados + '/' + t.unicos_total : '—'));
    tr.appendChild(celdaSiNo(t.completitud === 1, pct(t.completitud)));

    const dom = Object.values(t.dominios);
    tr.appendChild(celdaSiNo(dom.every((x) => x.cumple), dom.length ? 'dentro' : '—'));

    const h = Object.values(t.fk_respetadas)
      .reduce((a, f) => a + f.huerfanos, 0);
    tr.appendChild(celdaSiNo(h === 0, h ? h + ' huérfanas' : '0 huérfanas'));
    tbody.appendChild(tr);
  }
  tabla.appendChild(tbody);
  cont.appendChild(tabla);

  // Muestra de filas reales: la evidencia de que los datos no son inventados.
  for (const nombre of ['paciente', 'cita', 'medico']) {
    const filas = d.muestra[nombre];
    if (!filas || !filas.length) continue;
    const cols = estado.esquema.tablas[nombre].columnas.slice(0, 5);
    const bloque = document.createElement('div');
    bloque.className = 'muestra';
    const t2 = document.createElement('table');
    const cap = document.createElement('caption');
    cap.className = 'mini';
    cap.textContent = 'muestra de ' + nombre + ' (primeras ' + filas.length + ' de ' +
      d.lote.tablas[nombre].filas + ')';
    t2.appendChild(cap);
    const head = document.createElement('tr');
    for (const c of cols) {
      const th = document.createElement('th');
      th.textContent = c;
      head.appendChild(th);
    }
    t2.appendChild(head);
    for (const f of filas) {
      const tr = document.createElement('tr');
      for (const c of cols) {
        const td = document.createElement('td');
        td.textContent = f[c] === null ? '—' : String(f[c]);
        tr.appendChild(td);
      }
      t2.appendChild(tr);
    }
    bloque.appendChild(t2);
    cont.appendChild(bloque);
  }
}

function celdaNum(v) {
  const td = document.createElement('td');
  td.className = 'num';
  td.textContent = v;
  return td;
}

function celdaSiNo(bien, texto) {
  const td = document.createElement('td');
  const s = document.createElement('span');
  s.className = bien ? 'bien' : 'mal';
  s.textContent = (bien ? '✓ ' : '✗ ') + texto;
  td.appendChild(s);
  return td;
}

// ------------------------------------------------------------------ SQLite
function pintaSqlite(d) {
  const cont = $('#sqlite-out');
  cont.innerHTML = '';
  if (d.problemas.length) {
    const ul = document.createElement('ul');
    ul.className = 'lista-problemas';
    for (const p of d.problemas) {
      const li = document.createElement('li');
      li.textContent = p;
      ul.appendChild(li);
    }
    cont.appendChild(ul);
  } else {
    const ok = document.createElement('p');
    ok.className = 'bien';
    ok.textContent = '✓ PRAGMA foreign_key_check sin violaciones y sin claves repetidas.';
    cont.appendChild(ok);
  }

  const resumen = Object.entries(d.conteos)
    .map(([k, v]) => `${k}: ${v}`).join(' · ');
  $('#sqlite-resumen').textContent = resumen;

  const tabla = document.createElement('table');
  tabla.innerHTML = '<thead><tr><th>consulta sobre la base real</th><th class="num">resultado</th></tr></thead>';
  const tb = document.createElement('tbody');
  for (const [estadoCita, n] of Object.entries(d.citas_por_estado)) {
    const tr = document.createElement('tr');
    const a = document.createElement('td');
    a.textContent = 'citas por estado: ' + estadoCita;
    tr.appendChild(a);
    tr.appendChild(celdaNum(n));
    tb.appendChild(tr);
  }
  tabla.appendChild(tb);
  cont.appendChild(tabla);

  if (d.join_ejemplo.length) {
    const bloque = document.createElement('div');
    bloque.className = 'muestra';
    const t2 = document.createElement('table');
    const cap = document.createElement('caption');
    cap.className = 'mini';
    cap.textContent = 'JOIN de 4 tablas ejecutado sobre SQLite (paciente → cita → turno → médico → especialidad)';
    t2.appendChild(cap);
    const head = document.createElement('tr');
    for (const c of ['paciente', 'apellidos', 'especialidad']) {
      const th = document.createElement('th');
      th.textContent = c;
      head.appendChild(th);
    }
    t2.appendChild(head);
    for (const fila of d.join_ejemplo) {
      const tr = document.createElement('tr');
      for (const v of fila) {
        const td = document.createElement('td');
        td.textContent = v;
        tr.appendChild(td);
      }
      t2.appendChild(tr);
    }
    bloque.appendChild(t2);
    cont.appendChild(bloque);
  }
}

// ------------------------------------------------------------------ acciones
async function generar() {
  avisa('Generando lote…', 'trabajando');
  $('#btn-generar').disabled = true;
  try {
    const { status, datos } = await pedir('/api/generar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        semilla: parseInt($('#semilla').value, 10) || 0,
        volumenes: volumenesActuales(),
      }),
    });
    if (status !== 200 || !datos.ok) throw new Error(datos.error || ('HTTP ' + status));
    $('#resumen').textContent =
      datos.resumen.filas_totales + ' filas · semilla ' + datos.semilla;
    pintaMetricas(datos);
    avisa('Lote generado: ' + datos.resumen.filas_totales + ' filas en ' +
      datos.resumen.generado_en + '. Pulsa «Cargar en SQLite» para verificar en la base real.',
      'ok');
  } catch (e) {
    avisa('Error: ' + e.message, 'error');
  } finally {
    $('#btn-generar').disabled = false;
  }
}

async function cargarSqlite() {
  avisa('Creando la base SQLite y verificando integridad…', 'trabajando');
  $('#btn-demo').disabled = true;
  try {
    const { status, datos } = await pedir('/api/demo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        semilla: parseInt($('#semilla').value, 10) || 0,
        volumenes: volumenesActuales(),
      }),
    });
    if (status !== 200 || !datos.ok) throw new Error(datos.error || ('HTTP ' + status));
    pintaSqlite(datos);
    avisa(datos.problemas.length
      ? 'La base tiene ' + datos.problemas.length + ' problema(s).'
      : 'Base SQLite creada y verificada: 0 huérfanas, 0 claves repetidas.', 'ok');
  } catch (e) {
    avisa('Error: ' + e.message, 'error');
  } finally {
    $('#btn-demo').disabled = false;
  }
}

async function exportar() {
  avisa('Componiendo el script…', 'trabajando');
  try {
    const formato = $('#formato').value;
    const cuerpo = {
      semilla: parseInt($('#semilla').value, 10) || 0,
      volumenes: volumenesActuales(),
      formato,
    };
    if (formato === 'sql') cuerpo.motor = $('#motor').value;
    const { status, datos } = await pedir('/api/exportar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cuerpo),
    });
    if (status !== 200 || !datos.ok) throw new Error(datos.error || ('HTTP ' + status));
    estado.ultimoSql = datos.sql || datos.contenido;
    estado.nombreDescarga = datos.nombre;
    $('#sql').textContent = estado.ultimoSql;
    const lineas = estado.ultimoSql.split('\n').length;
    avisa('Script listo: ' + datos.nombre + ' · ' + datos.filas + ' filas · ' +
      lineas + ' líneas.', 'ok');
  } catch (e) {
    avisa('Error: ' + e.message, 'error');
  }
}

function descarga() {
  if (!estado.ultimoSql) { avisa('Primero genera un script.', 'error'); return; }
  const blob = new Blob([estado.ultimoSql], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = estado.nombreDescarga;
  a.click();
  URL.revokeObjectURL(a.href);
  avisa('Descargado: ' + estado.nombreDescarga, 'ok');
}

// ------------------------------------------------------------------ arranque
async function inicia() {
  $('#btn-generar').addEventListener('click', generar);
  $('#btn-demo').addEventListener('click', cargarSqlite);
  $('#btn-exportar').addEventListener('click', exportar);
  $('#btn-descargar').addEventListener('click', descarga);

  const { datos } = await pedir('/api/esquema');
  estado.esquema = datos;
  $('#esquema-titulo').textContent = datos.titulo;
  pintaVolumenes(datos);
  generar();
}

inicia();
