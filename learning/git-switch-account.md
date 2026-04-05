# Cambio de cuenta GitHub en terminal

Fecha: 2026-04-02

## Objetivo

Dejar este repositorio listo para usar otra cuenta de GitHub por HTTPS y asegurar que los commits usen el email `roger.macedo.m@uni.pe`.

## Estado que encontré

1. El remoto `origin` estaba configurado por HTTPS:

```bash
git remote -v
```

Resultado relevante:

```text
origin  https://github.com/rmacedo1194/peru-construcction-data-pipeline.git
```

2. El email global ya estaba configurado como:

```bash
git config --global --get user.email
```

Resultado:

```text
roger.macedo.m@uni.pe
```

3. Git estaba usando credenciales guardadas en disco:

```bash
git config --global --get credential.helper
```

Resultado:

```text
store
```

Eso significa que la cuenta usada para `push` y `pull` depende de la credencial guardada, no solo de `user.email`.

## Pasos ejecutados

### 1. Fijar el email de autor en este repo

```bash
git config --local user.email "roger.macedo.m@uni.pe"
```

Esto asegura que los commits en este repositorio salgan con ese email aunque el valor global cambie después.

### 2. Borrar la credencial HTTPS guardada para GitHub

```bash
printf "protocol=https\nhost=github.com\n\n" | git credential reject
```

Esto elimina la credencial almacenada para `github.com`. La siguiente vez que se haga `git push` o `git pull`, Git pedirá autenticación otra vez.

## Verificación

Verificar email local del repo:

```bash
git config --local --get user.email
```

Debe devolver:

```text
roger.macedo.m@uni.pe
```

Verificar remoto actual:

```bash
git remote -v
```

## Qué pasa después

En el próximo:

```bash
git push
```

Git pedirá login otra vez. Si el remoto sigue en HTTPS, normalmente GitHub pedirá un Personal Access Token en lugar de contraseña.

## Importante

- Cambiar `user.email` cambia el autor de los commits, pero no cambia la cuenta autenticada para subir o bajar código.
- Si la nueva cuenta no tiene acceso al repositorio `rmacedo1194/peru-construcction-data-pipeline`, el login no será suficiente.
- Si se quiere evitar tokens en HTTPS, conviene cambiar el remoto a SSH y usar una llave SSH asociada a la cuenta correcta.
