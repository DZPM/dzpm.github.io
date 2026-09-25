Title: Migración del blog
Date: 2009-04-02 23:41:20
Slug: migracion-del-blog
Tags: Django, Meta, Python, WordPress
Original_url: https://davidarcos.net/blog/2009/04/02/migracion-del-blog/

Como comentaba el otro día, he cambiado de hosting. Antes de nada, por favor suscribiros a [la nueva dirección del RSS](/blog/feed.xml) (la actual se mantendrá durante un tiempo, pero no garantizo que siga funcionando para siempre).

El cambio ha sido a mejor: el servidor compartido de Dreamhost daba una pings muy altos para España, una latencia horrible a la hora de gestionar por SSH, lentitud en servir las páginas, etc. Ahora este blog (y el resto de mis servicios) estan alojados en un servidor dedicado <span class="dead-link" title="Enlace roto: http://www.ovh.es/">OVH</span>, y la mejora en velocidad se nota muchísimo.

Me han pedido que hable de la migración, así que haré un resumen. En mi caso, fue complicado porque hice tres migraciones a la vez:

- Migración de servidor: No es excesivamente complicado: guardar los backups de cada proyecto, hacer dumps de las bases de datos, y restaurarlo en el servidor nuevo. Además, configurar en la máquina nueva los *vhosts* de apache y redireccionar los DNS para todos los dominios.
- Migración de directorio: Anteriormente el blog estaba en [http://www.davidarcos.net](/), mientras que ahora está en [http://www.davidarcos.net/blog](/blog/). Mediante reglas de *.htaccess* logro una redirección transparente, los enlaces externos existentes siguen llevando al artículo que toca y, como devuelve el código 301 (*Moved Permanently*), los buscadores no me penalizan por el cambio de URL. Por ese motivo el RSS antiguo sigue funcionando, aunque seguramente vuestro lector de feeds os habrá devuelto un montón de noticias antiguas, lo siento. Insisto: [actualizadlo](/blog/feed.xml), que algún día dejará de funcionar.
- Migración de versión de [WordPress](https://wordpress.org/): esta tenía bastante riesgo, pues estaba usando una versión muy desactualizada, no existían los tags ni los widgets, contenía varias tablas generadas por plugins (algunos incluso parcheados por mí...). Para hacer la migración no he seguido los pasos "clásicos" (restaurar backups y dumps, desactivar plugins, instalar versiones nuevas, etc), sino que he aprovechado el exportador/importador de WP. Los pasos a seguir:
    1. Antes de nada, eliminar todos los comentarios de spam. Esto servirá para aligerar muchísimo el tamaño del fichero resultante (con spam, ocupaba unos 20 Mb; sin spam, alrededor de 1,5 Mb)
    1. En el blog "antiguo", exportar mediante el gestor de WP. Se exportan entradas, páginas, categorías y comentarios.
    1. Descargar la última versión de WP, e instalarla. Ya tenemos blog nuevo.
    1. Ir al importador, e importar el archivo generado en el paso 2. Nota: el tamaño máximo del archivo es de 2Mb, así que es muy importante haber eliminado el spam. Si aún así se supera el tamaño, hay dos opciones: partir el archivo en varios (es XML, no es difícil), o bien modificar el código para que nos permita tamaños superiores a 2 Mb (tampoco es difícil, pero hay que ponerse el sombrero de sysadmin).
    1. Descargar la última versión del tema (yo uso [vSlider 3.2](https://irui.ac/cool-stuff/vslider3)), configurarla, añadir plugins y widgets a discreción.
    1. Sorpresa: el blogroll no se ha importado en el paso 2. Para importar, utiliza el formato opml: investigando un poco, resulta que el propio WP genera ese formato en /wp-links-opml.php.
    1. Los tags y yo teníamos una pelea pendiente. Por suerte WP trae de serie un componente, el *wp-cat2tag*, que como su nombre indica sirve para convertir las categorías existentes en tags. Funciona sin problemas. ¡Por fin una nube de etiquetas como el FSM manda!
    1. Me olvidaba, ¿te has fijado en la cabecera del blog? 😉

La actual versión de WP funciona de maravilla, parece se acabaron las sorpresas de incompatibilidades con plugins. Tenía previsto abandonar WordPress y migrar el blog a [ByteFlow](https://byteflow.su/) (un blog programado en [Django](https://www.djangoproject.com/)), pero se ha ganado la amnistía. Es una lástima, justo ahora que me he commiteado la <span class="dead-link" title="Enlace roto: http://hg.piranha.org.ua/byteflow/file/758d1f915cff/locale/es/LC_MESSAGES/django.po">traducción de Byteflow al español</span>...

Ya he tenido suficiente migración por una temporada. Lo próximo que haré será montar un entorno de desarrollo/producción de Django, y en cuanto tenga tiempo ir programando alguna cosilla. Por cierto, se aceptan ideas en los comentarios 🙂
