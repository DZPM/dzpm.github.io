Title: HOWTO SSHFS - Sistema de Ficheros SSH (for Dummies)
Date: 2007-01-21 22:40:14
Slug: howto-sshfs-sistema-de-ficheros-ssh-for-dummies
Tags: Howto, Software Libre
Original_url: https://davidarcos.net/blog/2007/01/21/howto-sshfs-sistema-de-ficheros-ssh-for-dummies/

En este artículo os voy a explicar una utilidad que considero bastante útil: **SSH-FS** (<span class="dead-link" title="Enlace roto: http://fuse.sourceforge.net/sshfs.html">**SSH FileSystem**</span>, Sistema de Ficheros SSH), que consiste en montar una partición remota vía SSH. Viene a ser como acceder a un servidor FTP, pero montado directamente en nuestro árbol de directorios. Y cifrado, por supuesto.

Conocimientos previos: saber usar un editor de texto, saber cual es tu nombre de usuario, y saber que nombre le vas a dar a "*REMOTO*" 😉

Al final de este tutorial, obtendrás dos comandos (montar_REMOTO, desmontar_REMOTO) con los que montarás/desmontarás el SSHFS. Y habrás aprendido un poquito de *ssh*, de *bash* (chown, chmod), de *bashcripting* y de *aliases* (.bash_rc).

## Configurar SSH para que no pida password

Lo hemos visto en el [HOWTO SSH sin password (for Dummies)](/blog/howto-ssh-sin-password-for-dummies/). Sigue las instrucciones del artículo, no hay mayor complicación.

<code></code>

## Instalar SSHFS

<code>apt-get install sshfs</code>

Y se descargará e instalará todo lo necesario.

## Preparar el punto de montaje

Tenemos que crear un directorio, y hacer que nuestro *usuario* sea el propietario. Lo normal sería montarlo en */media/algo*, así que tenemos que hacer las siguientes operaciones como *root*:

- Creamos el directorio:

<code>mkdir /media/REMOTO/</code>

- Cambiamos el propietario:

<code>chown USUARIO /media/REMOTO/</code>

Ahora nuestro usuario es el propietario del nuevo directorio, y podrá montar el sistema remoto ahí.

## Comprobar que funciona

- **Montar**: ejecutamos, como usuario:

<code>sshfs USUARIO@SERVIDOR:RUTA_REMOTA /media/REMOTO</code>

Donde *USUARIO* es nuestro nombre de usuario remoto,  
*SERVIDOR* es el servidor remoto (dominio o IP),  
*RUTA_REMOTA* es el directorio remoto que montaremos (por ejemplo /home/USUARIO),  
*/media/REMOTO* es donde vamos a montar el sistema de ficheros (lo acabamos de crear en el paso anterior.

- **Desmontar**: ejecutamos, como usuario:

<code>fusermount -uz /media/REMOTO/</code>

Donde */media/REMOTO* es el directorio donde hemos montado el sistema de ficheros.

## Crear scripts para hacerlo más usable

Sería un coñazo tener que memorizar esas líneas, ¿verdad? Y si queremos montar *varios* sistemas remotos (yo ahora mismo tengo 6 configuraciones distintas), ¿cómo evitaremos hacernos un lío?

Es necesario abstraer. Vamos a hacerlo en dos pasos: en primer lugar crearemos **bashscripts**, para montar/desmontar fácilmente, y en segundo lugar haremos **aliases**, para que se puedan llamar desde la consola.

### Bashcripts

Crearemos dos scripts de bash. Es recomendable guardarlos en un directorio específico, en mi caso guardo todos mis scripts en *~/bash*

- **Script de montar**

Creamos un archivo: montar_REMOTO.sh, con el siguiente contenido:

> \#!/bin/bash  
> REMOTE=<s>**TU_SERVIDOR_REMOTO**</s>  
> USER=**<s>TU_NOMBRE_DE_USUARIO_REMOTO</s>**  
> RUTA_REMOTA=**<s>/home/TU_USUARIO</s>**  
> RUTA_LOCAL=<s>**/media/REMOTO**</s>  
> echo "Intentamos montar $REMOTE..."  
> sshfs $USER@$REMOTE:$RUTA_REMOTA $RUTA_LOCAL

(Sí, tienes que modificar *lo que está tachado y en negrita* por tus propios datos)

Pongo la siguiente captura como ejemplo:

![](/images/posts/howto-sshfs-sistema-de-ficheros-ssh-for-dummies/montar.png)

Le damos **permiso de ejecución**:

<code>chmod +x montar_REMOTO.sh</code>

- **Script de desmontar**

Creamos un archivo: desmontar_REMOTO.sh, con el siguiente contenido:

> \#!/bin/bash  
> REMOTE=**<s>REMOTO</s>**  
> echo "Intentamos desmontar $REMOTE..."  
> fusermount -uz /media/$REMOTE/

Como antes, cambia *REMOTO* por tus datos: el directorio donde has montado el sistema SSHFS.  
Pongo la siguiente captura como ejemplo:

![](/images/posts/howto-sshfs-sistema-de-ficheros-ssh-for-dummies/desmontar.png)

Le damos **permiso de ejecución**:

<code>chmod +x desmontar_REMOTO.sh</code>

Bien, ahora tenemos dos scripts a los que podemos llamar para montar y desmontar:

<code>sh ~/bash/montar_REMOTO.sh</code>

<code>sh ~/bash/desmontar_REMOTO.sh</code>

Pero ¡queremos más!

### Aliases

Queremos llamarlos mediante un simple comando (*montar_REMOTO*, *desmontar_REMOTO*), para no tener que memorizar comandos largos con rutas 😉.Editamos el fichero *.bashrc*. El contenido de ese fichero se ejecuta cuando iniciamos un terminal, así que pondremos los *aliases* ahí dentro.  
<code>gedit ~/.bashrc</code>

Añadimos las siguientes líneas:

> alias montar_REMOTO='~/bash/montar_REMOTO.sh'  
> alias desmontar_REMOTO='~/bash/desmontar_REMOTO.sh'

Y ¡ya está! Cerramos el terminal y lo volvemos a abrir (para que recargue el *.bashrc*), o simplemente lo ejecutamos (<code>source .bashrc</code>)

Ahora, cada vez que ejecutemos los comandos, se montará/desmontará sin mayores complicaciones.

Dejad cualquier duda, sugerencia, o jamón de Guijuelo en los comentarios.
