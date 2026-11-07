# Recetas: carga inicial desde la planilla

Este documento acompaña la carga de las recetas de la planilla "Recetario Galia" en la
sección **Recetas** de Galia. Es para el dueño y para pastelería: dice qué se cargó, qué
falta completar, qué hay que confirmar y cómo correr la carga en producción.

La regla de la carga fue **no inventar nada**: lo que la planilla no dice quedó sin
cantidad o anotado como "a completar" (se ve como aviso en cada receta). Los posibles
errores se cargaron **tal cual** y están en la lista de dudas, para que pastelería
decida. Después, la cocinera corrige todo desde la app.

- Datos: `backend/scripts/data/recetario_galia.json` (la planilla pasada en limpio).
- Script: `backend/scripts/import_recetario.py`.

## Qué se carga

18 recetas: las 10 hojas de la planilla, con una receta por variedad en cookies (5) y
muffins (3), más 2 bases.

| Receta | Rendimiento cargado |
|---|---|
| Almíbar de cacao (base) | 1 tanda |
| Masa de muffins (base) | 1 tanda |
| Cookie red velvet | 6,5 unidades (lo dice la planilla; ver dudas) |
| Cookie chispitas de chocolate y frutos secos | 6,5 unidades |
| Cookie Nutella | 6,5 unidades |
| Cookie chispitas de chocolate | 6,5 unidades |
| Cookie pistacho | 6,5 unidades |
| Chipa | 20 unidades ("aproximadamente 20") |
| Muffin chispitas de chocolate | 14 unidades ("aproximadamente 14") |
| Muffin frutos rojos | 14 unidades |
| Muffin manzana y canela | 14 unidades |
| Crumble de manzana | a completar |
| Galletitas de nuez | a completar |
| Scones de queso | 12 unidades |
| Banoffee | a completar (la planilla dice "4/5 tarteletitas") |
| Matilda | a completar |
| Souffle de nuez | a completar |
| Torta Galia | a completar |

Los pasos siguen el formato de "Galletitas de Nuez": un título corto, la indicación
con el texto de la planilla, y temperatura, tiempo, punto y consejo **solo cuando la
planilla los dice**. Los textos se dejaron como están en la planilla (incluidas las
faltas y el "añade / nevera" de Banoffee) para que la cocinera los corrija.

## Bases extraídas

Solo se armó una base cuando la planilla la trae **idéntica** en varias recetas:

- **Almíbar de cacao**: igual en Torta Galia y Matilda (cacao amargo 2 cucharadas,
  azúcar 4 cucharadas, leche 200 ml, "dejar hervir 1 minuto").
- **Masa de muffins**: igual en los tres muffins (premezcla 1 kg, huevos 350 g, agua
  220 cc, aceite 300 g, huevo 1 unidad, y el paso de batir).

Las dos rinden "1 tanda": cada torta o tanda de muffins lleva la base entera, que es lo
que dice la planilla. Si más adelante se quiere usar la base en otra receta, hay que
cargarle el rendimiento real (en ml o g).

**No** se unificaron, porque la planilla las trae distintas:

- **Bizcocho de chocolate** (Torta Galia / Matilda): el polvo de hornear es 10 g en una
  y 12 g en la otra. Cada torta tiene su bizcocho.
- **Ganache / relleno** (Torta Galia / Matilda): cantidades muy distintas (ver dudas).
- **Masa de cookies**: la harina cambia en cada variedad (160, 170 o 200 g).

## A completar, por receta

Cada receta tiene esta lista en su aviso de "a completar". Además, todo ingrediente
sin cantidad aparece marcado en la receta.

- **Almíbar de cacao**: volumen real si se usa en otra receta; la planilla solo dice
  "dejar hervir 1 minuto", falta cómo se arma.
- **Masa de muffins**: en qué momento se agrega la premezcla.
- **Cookies (las cinco)**: confirmar el rendimiento de 6,5; cantidad de esencia de
  vainilla (salvo Nutella, que no la trae en la lista aunque el paso la nombra).
  Red velvet: para qué es cada chocolate blanco y la crema. Chispitas y frutos secos:
  "nuez y almendras" vienen juntas (40 g).
- **Chipa**: la leche viene como rango (200-230 ml).
- **Muffin chispitas de chocolate**: cuándo se agrega el chocolate.
- **Muffin frutos rojos**: cuándo se agregan los frutos rojos; qué se hace con la
  harina, la manteca, el azúcar y la sal; la sal es "una pizca".
- **Muffin manzana y canela**: cantidad de canela y cuándo se agrega. La manzana no
  tiene cantidad en la lista: se cargó la del paso (1 manzana rallada).
- **Crumble de manzana**: rendimiento; la manzana viene como rango (750/800 g); el
  queso del último paso.
- **Galletitas de nuez**: rendimiento; cantidad de vainilla; cantidades de crema,
  mermelada y dulce de leche del armado; huevos vs. yema.
- **Scones de queso**: temperatura y tiempo de horno (la planilla no los tiene); la
  leche es "a ojo" (la planilla dice "a ojota"); en qué paso va la sal gruesa.
- **Banoffee**: rendimiento (4/5 tarteletitas); bananas (2/3); faltan los pasos del
  relleno, la ganache y el armado.
- **Matilda**: rendimiento; cantidad de sal; armado y en qué momento va el almíbar.
- **Souffle de nuez**: rendimiento; cuándo se incorporan las claras; el azúcar para
  caramelizar las nueces no está en la lista.
- **Torta Galia**: rendimiento; cantidad de sal; armado completo (capas) y en qué
  momento va el almíbar.

Cantidades sin número ("pizca", "a ojo", "para decorar", rangos como "200-230 ml")
quedaron sin cantidad y con el texto original en la nota del ingrediente. Las
cucharadas y cucharaditas se cargaron como tales (por ejemplo "2 cditas." = 2
cucharaditas): Galia no las puede pasar a gramos, así que el costo de esos
ingredientes queda incompleto hasta que se cambien a gramos.

**Unidades que no se convierten.** Si un ingrediente está en una unidad que no se puede
pasar a la del insumo (por ejemplo gramos contra un insumo en unidades), la receta se
carga igual, pero ese ingrediente **no descuenta stock y su costo queda incompleto**
hasta corregir la unidad. Casos conocidos en la planilla:

- **Masa de muffins**: "Huevo 350 g" (el insumo Huevo va en unidad) y "Aceite 300 g"
  (el aceite se mide en ml).
- **Souffle de nuez**: "Nuez 5 unidad" (el insumo Nuez va en kg).

Ambas recetas lo avisan en su "a completar".

## Dudas para pastelería

1. **Galletitas de nuez**: la lista dice "2 huevos" y el paso 4 dice "agregar la yema".
   Se cargaron 2 huevos. ¿Van 2 huevos enteros, 2 yemas o una yema?
2. **Galletitas de nuez**: el paso dice "cortar 6 discos de 8 cm", pero la tanda tiene
   unos 1,2 kg de masa. ¿Cuántos discos (o alfajores) salen?
3. **Matilda**: la ganache lleva 500 g de chocolate y 600 g de crema (más 30 g de
   manteca y miel); en Torta Galia son 200 g y 250 g (y 5 g de manteca). ¿Está bien?
4. **Cookies**: "con esta proporción salen 6,5 cookies". ¿Es así?
5. **Crumble de manzana**: el último paso es "agregar queso por encima", pero la lista
   no trae queso. ¿Va queso? ¿Cuál y cuánto?
6. **Bizcocho de chocolate**: 10 g de polvo de hornear en Torta Galia y 12 g en
   Matilda. ¿Cuál es el correcto, o son distintos a propósito? Si es el mismo, se puede
   armar una base "Bizcocho de chocolate" para las dos.
7. **Cookies**: la harina cambia en cada variedad. ¿Es a propósito?
8. **Cookies**: "80 g aprox para las rellenas". ¿Cuáles son las rellenas y con qué?
9. **Cookie red velvet**: chocolate blanco dos veces (60 g y 90 g) y 30 g de crema.
   ¿Una parte es el relleno?
10. **Muffin frutos rojos**: harina, manteca, azúcar y sal sin ningún paso. ¿Es un
    crumble por encima?
11. **Muffins**: el paso de mezclar no nombra la premezcla. ¿Cuándo se agrega?
12. **Souffle de nuez**: ¿cuándo se incorporan las claras a punto nieve?
13. **Harinas**: la planilla dice "Harina 0000", "Harina" y "Harina común". Se
    cargaron como insumos distintos. ¿Son la misma?
14. **Chipa**: "Mandioca 1 kilo". ¿Es almidón (fécula) de mandioca?

## Productos e insumos

**Productos.** Cada receta se vincula al producto de Galia que se llame igual (sin
importar mayúsculas ni acentos). Vincular **no** activa el descuento de stock: eso se
activa a mano desde la receta, cuando esté revisada. Una receta queda sin vincular, y
aparece en el informe con el motivo, si:

- no hay un producto activo con ese nombre (esperable en cookies y muffins, que en la
  carta pueden tener otro nombre): se vincula a mano desde la receta;
- el producto ya tiene receta (por ejemplo, la composición que tenía antes y que se
  pasó a receta): la de la planilla se carga igual, sin vincular, y hay que decidir
  cuál vale. Si además se llaman igual, la de la planilla se carga como
  "<nombre> (planilla)";
- el producto ya descuenta stock sin receta: no se toca, se vincula a mano.

Las bases no se vinculan a ningún producto.

**Insumos.** Cada ingrediente se busca entre los insumos existentes por nombre, sin
importar mayúsculas, acentos, espacios ni singular/plural ("Huevo" encuentra
"Huevos"). El informe lista los que encontró con otro nombre, para revisarlos. Los
que no existen se crean **sin precio** (el costo queda incompleto hasta cargarlo), con
unidad kg, l o unidad según cómo los usa la planilla, o "a completar" si solo aparecen
en cucharadas o sin cantidad (sal, esencia de vainilla, canela, banana, miel).

Nombres que se ordenaron al pasar la planilla (el texto original quedó en la nota del
ingrediente cuando cambia algo): "Huevos" / "Huevo mediano" → Huevo; "Nueces" /
"Nueces caramelizadas" → Nuez; "Queso regianito" → Queso reggianito; "vainilla" →
Esencia de vainilla; "Café caliente" → Café; "Manzana cortada" → Manzana; "Chocolate
rallado" → Chocolate; "Crema chantilly" → Crema; "Pizca de sal" → Sal.

Insumos que usa la carga (se crean los que no existan): Aceite, Agua, Azúcar, Azúcar
blanca, Azúcar impalpable, Azúcar rubia, Banana, Bicarbonato, Cacao amargo, Café,
Canela, Chocolate, Chocolate blanco, Chocolate negro, Chocolate semiamargo, Colorante
RED, Crema, Dulce de leche, Esencia de vainilla, Frutos rojos, Harina, Harina 0000,
Harina común, Harina de almendras, Huevo, Leche, Mandioca, Manteca, Manzana, Mermelada
de frutos rojos, Miel, Nuez, Nuez y almendras, Nutella, Pasta de pistacho, Polvo de
hornear, Premezcla, Queso reggianito, Queso sardo, Queso tybo, Sal, Sal fina, Sal
gruesa. La lista exacta de los que se van a crear la da el informe de prueba.

## Antes de correrlo: chequeos en producción

Correr estas dos consultas primero y arreglar lo que devuelvan:

```
SELECT id,name,unit FROM supplies WHERE btrim(unit,' .')='';
```

Insumos cuya unidad no tiene letras: una unidad así deja de descontar stock.

```
SELECT id,name FROM products WHERE has_recipe AND track_stock;
```

Productos con receta y stock propio a la vez: guardar el vínculo desde el panel de la
receta los pasaría a stock de producto terminado.

## Cómo correrlo en producción

**Automático en el deploy.** `build.sh` corre
`python scripts/import_recetario.py --apply --if-empty` después de las migraciones.
Con `--if-empty` solo carga si todavía no hay ninguna receta (ni siquiera
desactivada). Así el recetario entra en el primer deploy y en los siguientes no se
hace nada, aunque la cocinera haya renombrado o editado recetas. El informe queda en
el log del build. Si la carga falla, el build sigue y el log muestra un `AVISO`. Si no
se pasa `--user-email`, figura como autor el primer admin activo.

**A mano** (por ejemplo, para probar otra versión del JSON): desde `backend/`, con `DATABASE_URL` de producción y la base ya migrada (con las
migraciones de recetas aplicadas). `--user-email` es un admin activo: figura como
quien cargó las recetas.

1. **Prueba** (no guarda nada, solo informa):

   ```
   python scripts/import_recetario.py --user-email <admin@...>
   ```

2. **Revisar el informe**: recetas nuevas, las que ya existían, vínculos con
   productos, las que quedan sin vincular y por qué, productos no encontrados, insumos
   que se crearían e insumos encontrados con otro nombre. Si un insumo o producto
   existe con otro nombre, conviene corregir el nombre en
   `scripts/data/recetario_galia.json` y volver a probar. Si hay errores, no se guarda
   nada: corregir y repetir.

3. **Guardar**:

   ```
   python scripts/import_recetario.py --user-email <admin@...> --apply
   ```

Se puede volver a correr sin riesgo: las recetas que ya existen (por nombre) no se
tocan, así que las correcciones que haga la cocinera en la app no se pisan.

Después de guardar:

- vincular a mano las recetas que quedaron sin producto;
- cargar los precios de los insumos nuevos;
- con pastelería, resolver las dudas y completar lo pendiente;
- recién con la receta revisada y con rendimiento, activar el descuento de stock del
  producto.
