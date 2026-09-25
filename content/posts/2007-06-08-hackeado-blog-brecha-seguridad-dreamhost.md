Title: Me han hackeado el blog: ¡brecha de seguridad con DreamHost!
Date: 2007-06-08 01:07:08
Slug: hackeado-blog-brecha-seguridad-dreamhost
Tags: Meta, Seguridad, WordPress
Original_url: https://davidarcos.net/blog/2007/06/08/hackeado-blog-brecha-seguridad-dreamhost/

> *Si ayer te preocupabas por qué mi blog estaba en blanco, o anteayer te preguntabas el por qué del iframe oculto con spam, he aquí la respuesta: me han hackeado el servidor. Y ni siquiera ha sido culpa mía... 😐*

Más de 3500 cuentas de DreamHost han sido comprometidas, por culpa de un fallo de seguridad de su panel de control web. Todavía no hay versión oficial que lo confirme.

## Consecuencias del ataque

Con dichas cuentas, efectuaban varios tipos de ataque, dependiendo del blog:

1. Dejar algunos/todos los index.php e index.html en blanco
1. Insertar iframes ocultos con basura en dichos archivos
1. Añadir código maligno (spam en links ocultos) al final de esos archivos.

Dicho patrón se repite para todos los archivos que se alojen en esa cuenta: en mi caso, han defaceado Hic sunt Trolls, Planet FiveMonkeys, ¡e incluso los backups de ambos!

## Consejos inmediatos

1. Cambia urgéntemente la **contraseña**
1. Descarta los backups que tenías online: en mi caso han modificado incluso esos archivos.
1. Comprueba todos los archivos **index.php** y **index.html**. Incluso el de dentro de wp-admin/.
1. Si has sufrido el mismo ataque, agradecería que dejes un comentario diciendo el servidor de DreamHost que usas. Yo estoy alojado en **dasani** (si usas **dasani** y no has sufrido el ataque, déjame también un comentario, por favor). Me gustaría investigar más acerca del ataque, dadme algo de lo que partir.

## Más información

Después de estudiar el ataque que me hicieron (había pocas pruebas) llegué a la conclusión de que el *h4ckeo* tenía que haber sido externo, o bien obra de ingeniería social sobre alguno de mis compañeros de hosting. Al descartar la segunda opción, me quedaba ante el sabotaje de dreamhost, pero sin pruebas que lo demuestren...

Vía jotape (gracias), me encuentro con la <span class="dead-link" title="Enlace roto: http://www.blog.armandososa.com/2007/06/06/hackeado/">explicación de Armando Sosa</span>, (le ha afectado en varios sitios que maneja), que confirma mis sospechas. A él también le han blanqueado varios inde.php

Armando cita a <span class="dead-link" title="Enlace roto: http://mezzoblue.com/archives/2007/06/05/unsettling/">Dave Shea</span>, parece haber sido el primero en descubrir la brecha de seguridad. En su caso fue diferente, supongo que por tener un blog de más PR: le han añadido enlaces ocultos a spam de drogas, que aparecían o desaparecían ¡según la hora del día! Impresionante lo que hacen los spammers para optimizar el efecto del spam. En los comentarios de su artículo se desvela la trama...

![](/images/posts/hackeado-blog-brecha-seguridad-dreamhost/jun4-spamlinks.gif)

 *"Regalito" que le han dejado a Dave...*

DreamHost no ha dado una **respuesta oficial**, si bien en DreamHostStatus hablan de <span class="dead-link" title="Enlace roto: http://www.dreamhoststatus.com/2007/06/06/security-breach/">la brecha de seguridad</span>. Espero, en breve, una respuesta razonable en el <span class="dead-link" title="Enlace roto: http://blog.dreamhost.com/">blog oficial</span>, o habrán perdido muchos puntos ante mí 🙁

En fin, con las medidas de seguridad tan paranoicas que suelo tomar, me sorprendió bastante que me *pwn3asen* el blog. Los logs suelen mostrar ataques de todo tipo (sin éxito), y como en este caso no supe el motivo, incluso los repasé uno a uno.

Encontrar que ha sido culpa de DreamHost es una mezcla de alivio y desgana: por una parte, *no era culpa mía*, por la otra, mi seguridad *no depende solamente de mí*. **La seguridad es una cadena que se rompe por el eslabón más débil.**
