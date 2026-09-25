Title: HOWTO SSH sin password (for Dummies)
Date: 2007-01-21 22:35:36
Slug: howto-ssh-sin-password-for-dummies
Tags: Howto, Software Libre
Original_url: https://davidarcos.net/blog/2007/01/21/howto-ssh-sin-password-for-dummies/

*Nota: Este artículo es una "introducción" para el [HOWTO SSHFS - Sistema de Ficheros SSH (for Dummies)](/blog/howto-sshfs-sistema-de-ficheros-ssh-for-dummies/). Antes de instalar SSHFS, configuraremos nuestra cuenta SSH de manera que no nos pida la contraseña: será mucho más cómodo.*

**SSH** ([*Secure Shell*](https://es.wikipedia.org/wiki/Secure_Shell)) permite iniciar una sesión segura en un ordenador remoto. O sea, te conectas a otra máquina, y trabajas como si estuvieras en tu propio ordenador local. Puedes administrar, subir/bajar archivos, poner cosillas a descargar, o hacer cualquier otra cosa que se te ocurra. Lo considero una utilidad imprescindible en cualquier sistema.

> [Definición de SSH en Wikipedia](https://es.wikipedia.org/wiki/Secure_Shell):
>
> **SSH** (**S**ecure **SH**ell) es el nombre de un [protocolo](https://es.wikipedia.org/wiki/Protocolo) y del [programa](https://es.wikipedia.org/wiki/Programa) que lo implementa, y sirve para acceder a máquinas remotas a través de una red. Permite manejar por completo el [ordenador](https://es.wikipedia.org/wiki/Ordenador) mediante un [intérprete de comandos](https://es.wikipedia.org/wiki/Int%C3%A9rprete_de_comandos), y también puede redirigir el tráfico de [X](https://es.wikipedia.org/wiki/X_Window_System) para poder ejecutar programas gráficos si tenemos un [Servidor X](https://es.wikipedia.org/w/index.php?title=Servidor_X&action=edit) arrancado.

Vayamos al grano:

## Instalar SSH

El *cliente de SSH* viene instalado en cualquier distribución, cacho <span class="dead-link" title="Enlace roto: http://revistes.upc.es/wiki/N00b">n00b</span> 😉. Por si lo hubieses desinstalado:

<code>apt-get install openssh-client</code>

El *servidor de SSH* solo lo necesita la máquina a la que te vas a conectar. Si eres el adminsitrador de esa máquina tienes que instalar openssh-server:

<code>apt-get install openssh-server</code>

¿Por que no viene instalado un servidor de SSH por defecto? Por la política "*Cero puertos abiertos*": por defecto no puede haber ningún puerto escuchando.

Para **comprobar que funciona**, basta con conectarse al servidor remoto:

<code>ssh USUARIO@SERVIDOR</code>

SERVIDOR también puede ser una dirección IP

![](/images/posts/howto-ssh-sin-password-for-dummies/ssh_01.png)

*(ejemplo:* *USUARIO= dzpm,* *SERVIDOR = dasani.dreamhost.com)*

Nos pide la contraseña, y entramos al servidor.

## Configurar SSH sin contraseña

Dos simples pasos:

- Generamos la clave pública del cliente. En el ordenador local, ejecutamos:

<code>ssh-keygen -t rsa</code>

Esto nos crea, en el directorio ~/.ssh, los archivos *id_rsa* y *id_rsa.pub*, que contienen la clave privada y la pública del ordenador cliente.

- Copiamos la clave pública del cliente al servidor, en un archivo de configuración donde se ponen las "claves autorizadas":

<code>scp .ssh/id_rsa.pub USUARIO@SERVIDOR:~/.ssh/authorized_keys</code>

*scp* (**Secure Copy**) es la versión de SSH usada para copiar ficheros de un servidor a otro. Obviamente también viaja cifrado.

![](/images/posts/howto-ssh-sin-password-for-dummies/ssh_02.png)

*Copiamos la clave pública del cliente al archivo "authorized_keys" del servidor*

- Ya está. A partir de ahora, cuando nos conectemos por SSH, ¡no nos pedirá contraseña! Comprúebalo:

<code>ssh USUARIO@SERVIDOR</code>

&gt; Continuar en *[HOWTO SSHFS - Sistema de Ficheros SSH (for Dummies)](/blog/howto-sshfs-sistema-de-ficheros-ssh-for-dummies/)*
