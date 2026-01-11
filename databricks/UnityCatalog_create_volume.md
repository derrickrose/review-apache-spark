# README — How to Create a Unity Catalog Data Volume in Databricks (Web UI Only)

This guide explains **step-by-step** how to fully configure Unity Catalog in Databricks and create a **data volume**, all using the **Databricks Web UI** (no CLI or code required).

---

## 1. Create Your Databricks Account (Free Trial)

1. Go to: https://www.databricks.com/try-databricks  
2. Choose **AWS**, then choose the region closest to you (e.g., **eu-west-3 Paris**).  
3. Complete account creation.  
4. This creates:
   - A Databricks **Account**
   - A Databricks **Workspace**

You are now the **Account Admin / Owner**.

---

## 2. Open the Account Console

Go to:  
**https://accounts.cloud.databricks.com/**

You must see this left menu:

- Workspaces  
- Catalog  
- User management  
- Security  
- Cloud resources  
- Settings  

If you don’t see this, you are not logged in as **Account Admin**.

---

## 3. Create a Metastore (Region: eu-west-3)

1. Go to **Catalog** (in Account Console left menu).  
2. Click **Create metastore**.  
3. Enter:
   - **Name:** `metastore_aws_eu_west_3`
   - **Region:** `eu-west-3 (Paris)`
   - **Storage root:** accept auto‑created bucket  
4. Click **Create**.

---

## 4. Assign Yourself as Metastore Admin

1. Open your new metastore.  
2. Find **Metastore Admin**.  
3. Click **Edit** → Add your email → Save.

This gives permission to create catalogs, schemas, volumes, etc.

---

## 5. Assign the Metastore to Your Workspace

1. In Account Console, go to **Workspaces**.  
2. Click your workspace name.  
3. Click **Assign Metastore**.  
4. Choose `metastore_aws_eu_west_3`.

Unity Catalog is now activated for your workspace.

---

## 6. Open Your Workspace UI

Click **Open workspace** from the workspace page.

Inside the workspace, open the left sidebar → **Catalog**.

---

## 7. Create a Catalog (Web UI)

1. Click **Catalog** in the left menu.  
2. Click **Create Catalog** (top‑right).  
3. Choose:
   - **Type:** Standard  
   - **Name:** `main` (recommended)  
4. Click **Create**.

Your catalog now appears under **My organization**.

---

## 8. Use the Default Schema

Inside:

```
My organization  
   main  
      default
```

The `default` schema is created automatically and is OK to use.

---

## 9. Create a Data Volume (Web UI)

Inside **main → default**:

1. Click **Create** (top right).  
2. Select **Volume**.  
3. Enter:
   - **Name:** `main_volume`
   - **Type:** Managed Volume  
4. Click **Create**.

Your Unity Catalog volume is now available at:

```
/Volumes/main/default/main_volume/
```

---

## 10. Upload a File Into the Volume (Web UI)

1. Open the volume (`main_volume`).  
2. Click **Upload to this volume**.  
3. Choose any file — CSV, JSON, TXT, image, etc.

The uploaded file now lives under UC governance.

---

## Optional: Use a Notebook for Validation

### Write a test file:

```python
dbutils.fs.put("volume://main.default.main_volume/test.txt", "Hello from Unity Catalog!")
```

### List files:

```python
dbutils.fs.ls("volume://main.default.main_volume")
```

### Read file:

```python
spark.read.text("volume://main.default.main_volume/test.txt").show()
```

---

## 🎉 Finished!

You now have:

✔ Metastore in **eu-west-3**  
✔ You as **Metastore Admin**  
✔ Workspace linked to the metastore  
✔ Catalog `main`  
✔ Schema `default`  
✔ Volume `main_volume`  
✔ File successfully uploaded  

You are fully ready to use Unity Catalog for:
- data ingestion  
- Delta tables  
- machine learning  
- external volumes  
- governance & permissions  

---

If you'd like, I can also generate a PDF version or add diagrams.  
