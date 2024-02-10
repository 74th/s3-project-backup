# S3 Project File Backup Tool

This tool wraps aws cli.

## how to use

### create config file `s3-project-backup.json`

```json
{
  "aws_profile": "nnyn-project-backup",
  "s3_bucket": "nnyn-project-backup",
  "s3_path_prefix": "20240210-nnyn-project-backup-testing",
  "s3_storage_class": "STANDARD"
}
```

you can use init command

```shell
s3-project-backup init
```

### upload directory files

```shell
s3-project-backup upload
```

or

```shell
s3-project-backup
```

### download directory files

```shell
s3-project-backup download
```

## default command

If there are no files in the directory, it works as the command download. If there are files in the directory, it works as the command upload.
