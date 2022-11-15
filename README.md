# segRedes-lab3

## Autores
* Alejandro Gálvez Ruiz (alejandro.galvez@alu.uclm.es)

## Explicación
El proyecto trata del desarrollo de una **API RESTFUL** sencilla que implementa ciertas **medidas de seguridad** vistas en clase tales como el cifrado de mensajes mediante **TLS sobre HTTP** o los archivos **_shadow_** para almacenar usuarios y sus contraseñas.

El funcionamiento de esta version de API RESTFUL es muy simple:
 * Cada persona podrá darse de alta con **_/signup_**. Esto **creará** o **actualizará** un archivo _shadow_, cuya ruta está especificada en una constante en el código del _server.py_, con el formato **_usuario_:$_hash_algorithm_$_hashed_password_**. Por defecto el algoritmo de hash usado es el SHA512.
 En caso de encontrar un usuario con el mismo nombre registrado devolverá un error 401, por lo tanto el programa **no permitirá crear ususarios duplicados**.

 * Cada usuario podrá iniciar sesión con **_/login_**. Esto comprobará que el ususario existe **comparando los hashes** de la contraseña aportada con la asociada a dicho ususario en el archivo _shadow_. Si todo es correcto logueará al ususario en el sistema, siempre y cuando este no lo estuviera ya.
 
 * Una vez en el sistema, el ususario puede desde **_/<username>/<doc_id>_** crear, actualizar, eliminar y hasta obtener uno o todos sus archivos _json_ sustituyendo <doc_id> por _all_docs.
 Estos archivos se almacenan en el servidor en _<ruta_raiz>/<username>/<doc_id>_. Donde _<ruta_raiz>_ es un argumento a la hora de lanzar el server.
 
En cualquier caso, todos los usuarios que inicien sesión en el sistema obtendrán un **token de sesión** de 5 minutos de expiración. Siempre que un usuario quiera accedes a sus archivos _json_ tendrá que aportar este token en la cabecera con el nombre **Authorization**.
Pasados los 5 minutos, un hilo despertará y eliminará este token, por lo que los usuarios deberán **loguear de nuevo** en el sistema.

## Certificados
Debido a que queremos una **comunicación cifrada** entre servidor y cliente a través del protocolo HTTPS, es necesario hacer uso de certificados que nos aseguren la autenticidad del servidor. Para ello existen las **CAs** o Certification Authorities. Esto son **terceras entidades** que firman estos certificados de manera que el cliente pueda confiar en que el servidor al que ellos acceden es el **correcto**.

Sin embargo, obtener estos certificados firmados por CA requiere un tiempo de espera y en muchos casos un pago económico.
En mi caso, y ya que solo crearemos un servidor de prueba que utilizaremos entre nosotros mismos, simplemente **generaré un certificado autofirmado**. De manera que la **autenticidad** de la comunicación solo podrá validarse en caso de estar seguro que el certificado ha sido entregado **íntegramente** por mi, el creador de este servidor y del certificado autofirmado.

La obtención e instalación de estos certificados en Ubuntu está descrito en su pagina oficial (https://ubuntu.com/server/docs/security-certificates), por lo que omitiré explicar como he generado mi certificado autofirmado y pasaré directamente a su instalación

### Instalación certificado

Desde el cliente, es necesario añadir el certificado autofirmado en el directorio de estos para poder comunicarnos con el servidor sin problema. Para ello añadimos el certificado al directorio _/usr/local/share/ca-certificates/_ con:

```
sudo cp <server.crt> /usr/local/share/ca-certificates/
sudo update-ca-certificates
```
Donde <server.crt> es el certificado autofirmado. 

En caso de utilizar el certificado provisto por mi en la carpeta _cert/_ bastará con ejecutar:

```
sudo cp cert/server.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

En caso de que haya creado un certificado autofirmado propio para probar el sistema, sustituya <server.crt> por su ruta. Recuerde que si va a seguir por esta vía, deberá cambiar la ruta del certificado y la llave pública que se pasa al servidor al lanzar su script. Esto es, las constantes

```
CERT_PATH = "cert/server.crt"
CERT_KEY_PATH = "cert/server.key"
```

## Resolver myserver.local

El programa servidor se asumirá en el endpoint https://myserver.local:5000 donde myserver.local resolverá a 127.0.0.1.
Para ello es necesario modificar el fichero

```
/etc/hosts
```
y en la linea

```
127.0.0.1 localhost
```
añadir _myserver.local_

```
127.0.0.1 localhost myserver.local
```

Este paso es importante puesto que mi certificado provisto solo funcionará para este dominio _myserver.local_.

## Ejcución del servidor
 
 Crea un entorno virtual y activalo:
```shell
python3 -m venv .venv
source .venv/bin/activate
```

Instala todas las dependencias:
```shell
pip install -r requirements.txt
```

Para lanzar el servidor ejecute el siguiente comando:
```
python3 server_script.py -r <root_directory>
```
Donde _<root_directory>_ es el directorio donde se almacenarán los ficheros _json_ de los usuarios.

Además, en caso de hacer uso del certificado que yo proveo, será necesario introducir su _passphrase_: **_segredes_**.
