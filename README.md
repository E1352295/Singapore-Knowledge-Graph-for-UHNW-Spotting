# UHNW Prospect Identification System – MVP Setup Guide

This guide provides a step-by-step walkthrough for setting up the MVP (Minimum Viable Product) of the AI-powered UHNW (Ultra-High-Net-Worth) prospect identification system. The entire setup runs **locally on a Windows 11** machine, leveraging Docker and various tools. We will cover everything from prerequisites and installations to workflow configurations and troubleshooting. The goal is to enable a non-technical user to get the system up and running and understand its components.

## 1. Prerequisites

Before setting up the system, ensure the following prerequisites are met:

- **Hardware**: A modern Windows 11 PC. At minimum, a dual-core CPU and **16 GB RAM** (32 GB+ recommended for smoother operation). Ensure you have at least **70 GB of free disk space** for Docker images and data.
- **Operating System**: Windows 11 (64-bit). Ensure Windows is updated. Windows 11’s integration with WSL2 (Windows Subsystem for Linux) will be used for Docker.
- **Internet Access**: A stable internet connection is required to download Docker images, install Python packages, and for the system to crawl data sources and connect to cloud services (Neo4j Aura DB, LLM API, etc.).
- **Docker Desktop**: Admin rights to install software and **Docker Desktop for Windows**.
- **Accounts & API Keys**:
  - **Neo4j AuraDB**: Sign up for a free Neo4j AuraDB account (Aura Free tier) and be ready to create a database instance. You will obtain a Neo4j **connection URI**, a **username** (usually `neo4j`), and an **auto-generated password** – save these credentials securely.
  - **LLM API Access**: The system’s NLP pipeline uses a Large Language Model for NER (Named Entity Recognition) and relation extraction. In our setup, we used *Google’s Generative AI API (e.g. PaLM/Gemini)*, which requires a Google Cloud project API key. Alternatively, you could use an OpenAI API key if configured as such. Ensure you have the appropriate API key and access for the LLM service.
  - **Other Accounts**: No special login is needed for data sources like MAS, SGX, or Wikidata since we use public data. All MAS and SGX data used are publicly available (MAS financial institution directory, SGX company reports) and Wikidata is open. Forbes richest list data is also public.

**Networking note**: If your PC is behind a corporate firewall or VPN, ensure Docker can access the internet. Also confirm that you can reach Neo4j’s cloud endpoints (Aura) on port 7687 (for the Bolt protocol) or HTTPS, as well as any API endpoints (Google APIs, etc.). 

## 2. Install Docker Desktop on Windows 11

We will use Docker to containerize the n8n workflow automation tool. Docker Desktop provides an easy way to run containers on Windows:

1. **Download Docker Desktop**: Visit the official Docker website and download **Docker Desktop for Windows**. Run the installer and follow prompts. During installation, **enable WSL2** integration (this allows Docker to run using the Windows Subsystem for Linux). If prompted, restart your system to finalize installation.
2. **Verify Installation**: After install, launch Docker Desktop. You should see the Docker whale icon in your system tray. Open a PowerShell or Command Prompt and run: `docker --version`. You should get a version output confirming Docker is installed.
3. **WSL2 Backend**: Ensure WSL2 is enabled (Docker prompts this on install for Win10/11). You can verify by opening Docker Desktop settings > *General* > and confirming “Use the WSL 2 based engine” is checked.
4. **Resources**: Docker will allocate resources (CPU, memory) for WSL2. By default it’s usually adequate, but if you plan heavy use (processing large files in containers), consider increasing the memory in Docker settings (e.g., 4 GB). For our MVP, default settings should suffice.

No other software installations are needed for now – we will use Docker to run n8n and possibly our Python components. Windows-specific tools (like Python or Node) are optional unless you plan to run parts of the pipeline outside of Docker. In general, we’ll aim to run everything through Docker/n8n for consistency.

## 3. Launch n8n (Workflow Orchestrator) in Docker

**n8n** is a workflow automation tool that we use to orchestrate data collection, processing, and loading tasks (the “ETL and scoring” pipeline). We will run n8n as a Docker container.

### 3.1 Pull the n8n Docker Image

Open a PowerShell terminal (or Windows Terminal) and pull the latest n8n image from Docker Hub by running:

```bash
docker pull n8nio/n8n:latest
```

This will download the n8n image to your machine.

### 3.2 Run the n8n Container

Now run the container. We want n8n to persist data (like saved workflows and credentials) between restarts, so we’ll use a Docker volume to store n8n’s data directory. We also need to expose n8n’s web interface port (default **5678**).

**Steps:**

1. **Create a volume** for n8n data persistence (optional but recommended):  
   ```bash
   docker volume create n8n_data
   ``` 

2. **Run n8n container** using the created volume:  
   ```bash
   docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
   ```  
   Let’s break down this command:
   - `-d` runs the container in detached mode (in the background).
   - `--name n8n` gives the container a friendly name “n8n”.
   - `-p 5678:5678` maps port 5678 on your PC (host) to port 5678 in the container, which is where n8n’s web UI runs.
   - `-v n8n_data:/home/node/.n8n` mounts the Docker volume `n8n_data` at n8n’s data directory inside the container. This ensures all workflows and credentials you create in n8n are saved persistently.
   - `n8nio/n8n` is the image name (using latest tag by default).

   > *Alternatively:* Instead of a named volume, you can bind-mount a host folder. For example, `-v "%UserProfile%\.n8n":/home/node/.n8n` would use a `.n8n` folder in your user directory. The named volume approach above is simpler as it abstracts the path.

3. **Check that n8n is running**: After a few seconds, run `docker ps` to see active containers. You should see `n8nio/n8n` in the list. If it’s not running (`docker ps -a` shows it exited), check logs with `docker logs n8n` for errors.

4. **Access the n8n UI**: Open a web browser and navigate to **http://localhost:5678**. You should see the n8n workflow editor interface. By default, n8n on localhost does not require login and will open the Editor UI directly. Keep this page open for the next steps.

   *If you get a connection error:* ensure no other service is using port 5678 and that Docker is running. Also check if your firewall is blocking local ports (usually not for localhost access).

### 3.3 (Optional) Secure the n8n instance

Since this is a local setup for MVP, it’s not mandatory to set up credentials for the n8n UI. However, if this machine is multi-user or you prefer to password-protect n8n, you can enable basic auth:
- Stop the n8n container: `docker stop n8n`
- Run it with environment variables for authentication, e.g.:  
  ```bash
  docker run -d --name n8n -p 5678:5678     -v n8n_data:/home/node/.n8n     -e N8N_BASIC_AUTH_ACTIVE=true     -e N8N_BASIC_AUTH_USER=<choose-user>     -e N8N_BASIC_AUTH_PASSWORD=<choose-strong-password>     n8nio/n8n
  ```  
  Replace `<choose-user>` and `<choose-strong-password>` accordingly. Now the n8n UI will prompt for this username/password on load.

For our purposes, you can keep it open (especially if offline or on a secure network). If enabling auth, remember to share the credentials with the team.

## 4. Setting Up Credentials in n8n

Within n8n, some nodes will require credentials (e.g., to connect to Neo4j or external APIs). n8n provides a **Credentials** management system to store sensitive keys/tokens securely and reuse them in workflows.

To add credentials in n8n:

1. In the n8n Editor UI, find the **Credentials** tab. In recent n8n versions, this is usually accessible via the left side menu (key icon) or when configuring a node that requires credentials.
2. Click **“New”** or **“Create a new credential”**. You will see a list of credential types.
3. **Neo4j AuraDB**: n8n doesn’t have a built-in Neo4j node, but we can store Neo4j credentials using the **HTTP Basic Auth** credential type (since we will interact with Neo4j via its HTTP API). Choose **“HTTP Basic Auth”**:
   - Set “Credential Name” (e.g., `Neo4j Aura Free`).
   - **Username**: `neo4j` (the default user for AuraDB, unless you set a custom user).
   - **Password**: *Your Aura-generated password* (copied when you created the instance).
   - Save the credential.
   - We will use this credential in the HTTP request node when sending Cypher queries to Neo4j.
4. **LLM API Key**: If using an external API for the LLM:
   - For **Google PaLM/Gemini API**: This uses an API key in a header or as part of a library call. We might handle this in a Code node or via environment variables (see Section 9). If using via HTTP, you can store it as an **Generic “API Key” credential** if a node requires, or simply as a variable in the workflow.
   - For **OpenAI API** (if that were used): n8n has an **OpenAI node** where you’d create an OpenAI credential (needs API key).
   - Alternatively, store such keys in a **“.env” file** for Python scripts (discussed later).
5. **Other Credentials**: The data sources (MAS, SGX website, Forbes, Wikidata) do not require login. Wikidata queries can be done openly. MAS directory is public. Forbes list we will handle as a static or scraped data. So no other credentials needed for those.

**Storing credentials securely**: n8n encrypts credentials in its database (or file storage) so you don’t have to hard-code them. Avoid putting secrets directly in workflow nodes if possible; use the Credentials mechanism or environment files. Also, do not commit these to any repository. For example, we set up environment variables for Neo4j and API keys in our development `.env` file and code – we will mimic that setup where applicable.

*(If you prefer, you can skip storing Neo4j creds in n8n and instead directly include them in the HTTP request nodes as Basic Auth header for simplicity. But using Credentials is cleaner and more secure.)*

## 5. Configuring n8n Workflows (Step-by-Step)

With n8n running and credentials ready, we will configure the workflows that perform data extraction, transformation, and loading (ETL) for each data source, as well as the scoring pipeline. The system uses three main data sources plus an LLM-based extraction step:

- **A. MAS** – Monetary Authority of Singapore Financial Institutions Directory (key personnel of banks/insurers).
- **B. SGX** – Singapore Exchange listed companies’ Annual Reports (Board of Directors info from PDFs).
- **C. Forbes + Wikidata** – Forbes “Singapore Rich List” as seed persons, with Wikidata to get family relations.
- **D. (Integration & Scoring)** – Consolidation of extracted data, pushing to Neo4j, and calculating UHNW scores.

We will set up separate sections or sub-workflows for each data source (A, B, C) and then a final step for scoring (D). This modular approach makes it easier to run updates for each source independently.

> **Note:** The actual n8n workflows have been pre-built during development. Here we will outline how to recreate them. If you have the exported JSON for these workflows (in the repository or provided separately as “N8N Workflows Setup”), you can import them directly (n8n Editor Menu → Import workflow). Otherwise, follow the steps below to build them.

### 5.1 MAS Key Personnel Ingestion Workflow

**Goal**: Crawl the MAS Financial Institutions Directory to retrieve key personnel (names and roles like CEO, Director, etc.) for each institution, and load those Person–Company relationships into Neo4j.

**Data Source**: MAS publishes an online directory of licensed financial institutions in Singapore. Each institution (e.g., banks, insurance companies) has a page listing its **“Key Individuals”** (directors, CEO, etc.). These are high-value signals because someone holding a top position in a financial institution is likely a HNW individual or connected to wealth.

**Workflow Outline**:
1. **Trigger** – We can use a **Manual Trigger** node to start this workflow on demand, or schedule it (e.g., Cron node to run weekly or monthly since the directory updates periodically). For testing, add a **Manual Trigger** node (this does nothing except allow manual execution in the editor).
2. **Fetch Institution List** – The MAS directory might have an index or list of institutions. In our MVP, if we don’t have an index URL, we might maintain a list of relevant institution URLs to crawl (e.g., a static list of major banks). For completeness:
   - Add an **HTTP Request** node, name it “Get MAS Institutions”. Configure it to GET the listing page (for example, MAS might have a page listing banks or an API endpoint). If an index isn’t available, you can skip directly to known pages.
   - If a listing is fetched, you’d then parse it (using HTML parsing) to get links for each institution’s detail page.
   - If we have a predetermined list of URLs (perhaps curated), we can inject them via a **Code** node or static data.
3. **Fetch Key Personnel Pages** – Use an **HTTP Request** node inside a loop to fetch each institution’s detail page:
   - You can use n8n’s **Split In Batches** node or **Loop** functionality. For example, if the previous step returned an array of URLs, connect it to a Split In Batches set to batch size 1, which will pass each URL one by one.
   - Inside the loop, an HTTP Request node (e.g., “Fetch Institution Page”) uses an expression for the URL (coming from the batch). The result will be the HTML of that institution’s page.
   - Add a short **wait** between requests if needed (to avoid hammering the MAS site too quickly – e.g., a 1-second Wait node between batches, as a throttle).
4. **Parse HTML for Key Personnel** – Once we have the HTML content:
   - Add an **HTML Extract** node (community node) or use a **Code** node with custom parsing. The HTML Extract node allows you to apply CSS selectors to extract elements. Configure it to extract the names and roles from the “Key Individuals” or “Key Persons” table. For instance, if the page structure has a table of key personnel, target the table rows for Name and Title columns.
   - Since n8n's **Code** node does not support external libraries like `cheerio`, the parsing must be done using a series of native **HTML** nodes.

     **Step 1: Extract Main Content**
     - After fetching the institution's detail page with an `HTTP Request` node, add an `HTML` node to extract the main content blocks.
     - **Extraction 1**: Extract the company name.
       - **Key**: `Company Name`
       - **CSS Selector**: `.title h1`
       - **Return Value**: `Text`
     - **Extraction 2**: Extract the HTML for each key personnel entry.
       - **Key**: `Personnel`
       - **CSS Selector**: `.personnel`
       - **Return Value**: `HTML`
       - **Return Array**: `true`

     **Step 2: Extract Personnel Details**
     - Add another `HTML` node to process the `Personnel` array extracted in the previous step.
     - **Input Data Field**: Set this to `Personnel` to tell the node to parse the HTML within that field.
     - **Extraction 1**: Extract the person's title.
       - **Key**: `Person Title`
       - **CSS Selector**: `.header-inner-2`
       - **Return Value**: `Text`
     - **Extraction 2**: Extract the person's name.
       - **Key**: `Person Name`
       - **CSS Selector**: `.font-resize`
       - **Return Value**: `Text`

     This multi-step process first isolates the relevant sections of the page and then extracts the specific details, achieving the same result as the conceptual `cheerio` script but using only native n8n functionality.
   - The result of this process is structured data that can be output as a CSV file. The data will have the following header: `Company Name,href[0],Person Title,Person Name`.
   - An example row would look like this:
     `DBS GROUP HOLDINGS LTD,https://eservices.mas.gov.sg/fid/institution/detail/3671-DBS-GROUP-HOLDINGS-LTD,Chief Executive Officer,Piyush Gupta`
   - **Note:** The `href[0]` column contains the URL for the institution's detail page, which provides provenance for the data.
5. **Load into Neo4j** – Now we have structured data. We need to insert or update our graph database:
   - We can accumulate all the results (after the loop completes, use a **Merge** node to gather all items from the split batches back into a single list).
   - **Primary Method: Use `Execute Command` node to run a Python script**
     - Neo4j AuraDB instances use the Bolt protocol (`neo4j+s://`), which cannot be accessed directly with n8n's `HTTP Request` node. The correct and most robust method is to use a Python script with the official `neo4j` driver, as demonstrated in the project's `load_graph_v_5.py` script.
     - In your n8n workflow, after generating the CSV data, use a **Read/Write Files from Disk** node to save it to a location accessible by the n8n container (e.g., `/files/mas_personnel.csv`).
     - Add an **Execute Command** node to run the Python ingestion script, passing the path to the saved CSV file as a command-line argument.
     - **Setup**:
       - Ensure your n8n execution environment has Python and the `neo4j` library installed. If using the provided Docker setup, you can add `neo4j` to the `requirements.txt` file.
       - The Python script should read credentials from environment variables for security, just like `load_graph_v_5.py` does.
       - The command in the node would look something like: `python /path/to/ingestion_script.py /files/mas_personnel.csv`
     - The script itself would contain the connection logic and Cypher queries to process the CSV:
       ```python
       # Example Python ingestion script snippet
       import os, sys, csv
       from neo4j import GraphDatabase

       NEO4J_URI = os.getenv("NEO4J_URI")
       NEO4J_USER = os.getenv("NEO4J_USER")
       NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

       driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

       # Get CSV file path from command-line argument
       if len(sys.argv) < 2:
           print("Error: CSV file path not provided.", file=sys.stderr)
           sys.exit(1)
       csv_file_path = sys.argv[1]

       # Cypher query to merge data from the CSV
       cypher_query = """
       UNWIND $rows AS r
       MERGE (p:Person {name: r.`Person Name`})
       MERGE (c:Company {name: r.`Company Name`})
       MERGE (p)-[rel:HAS_ROLE_AT {role: r.`Person Title`}]->(c)
       ON CREATE SET rel.source = 'MAS', rel.url = r.`href[0]`
       """

       with driver.session() as session:
           with open(csv_file_path, 'r', encoding='utf-8') as f:
               reader = csv.DictReader(f)
               rows = list(reader) # Load all rows into a list
               session.run(cypher_query, rows=rows)

       driver.close()
       print(f"Successfully processed {len(rows)} rows from {csv_file_path}")
       ```


6. **Finalize**: Name this workflow “MAS Key Personnel to Neo4j” (for example). Test it by executing (click “Execute Workflow”). It should fetch one or more pages and eventually insert data into Neo4j. Check the n8n execution log for any errors at each node.

   After running, you can verify in Neo4j Browser (see Section 6) with a query like: `MATCH (p:Person)-[:HAS_ROLE_AT]->(c:Company) RETURN p.name, c.name, count(*)`. You should see the new Person and Company nodes created. Each relationship has properties like `role`, `source="MAS"`, etc.

**Note on normalization**: The workflow does basic cleanup (trimming spaces, etc.). Our design also included standardizing company name formats (e.g., “Ltd.” vs “Limited”) and person name casing. In this MVP, ensure consistency manually:
- If you see duplicate nodes for what should be the same entity (e.g., “UOB Ltd” vs “United Overseas Bank Limited”), you might need to merge them later or adjust the parsing logic to normalize names. The MVP script uses exact matches (unique constraint on name), so consistency is key. We handled common variants by simple string replacements (e.g., drop “Ltd.”).

Now MAS data is flowing into the graph. Next, SGX.

### 5.2 SGX Annual Reports Workflow

**Goal**: Extract board of directors and related info from SGX-listed company annual reports (PDFs) using an LLM for NER (entity extraction) and relation extraction (detecting which person is a director of which company).

**Data Source**: SGX (Singapore Exchange) requires listed companies to publish Annual Reports. These are rich PDFs containing sections like “Board of Directors” with names and roles of company directors. We target these sections to find potential HNW individuals (e.g., a person on multiple boards, or in a CEO/Chairman role of a public company).

**Challenge**: The data is unstructured (PDF text). We will use a combination of text extraction and an LLM to parse the content:
- Extract text from PDF (especially the part listing board members).
- Use an LLM with a prompt to identify Person names, Company names, and roles, and output structured JSON.

**Workflow Outline**:
There are a few ways to approach this in n8n. Because PDF processing and calling an LLM can be complex, one approach is to offload this to a Python script. However, we can orchestrate it via n8n by either calling a local script or using API-based tools:
1. **Trigger** – Could be manual or scheduled (e.g., to run when a new annual report is released). For testing, use Manual Trigger.
2. **List/Provide PDFs** – Determine how to get the PDF files. Options:
   - **Automatic download**: If you have a list of URLs for annual reports (from the company’s investor relations site or SGX announcements feed), you could have n8n fetch them. For MVP, it might be simpler to manually download a few example PDFs into a local folder.
   - For demonstration, copy a PDF file (e.g., `SIA_Engineering_AnnualReport2024.pdf`) into a known folder on your Windows (or mount it in Docker if needed).
   - If you want n8n to handle download: Use HTTP node to fetch the PDF URL (you’ll get binary data), then use n8n’s **Move Binary Data** node to save it to disk or keep as binary.
3. **PDF Text Extraction** – n8n does not natively parse PDFs to text. We have two approaches:
   - **Use a Command**: Utilize an external tool via **Execute Command** node. For example, if `pdftotext` utility or Python’s PDF libraries are available. This requires our n8n container to have such tools. (In our project’s dev environment, we used Python libraries like `pdfplumber` to extract text.)
   - **Custom Script**: Write a short Python script to read the PDF and return text. If using n8n Execute Command, you could call `python extract_text.py <file>` and capture output.
   - **Manual**: For MVP, as a simpler route, you might manually extract or copy the relevant text (since we’re focusing on setup, not the heavy coding).
   - *In our actual pipeline, this step is implemented in code, not pure n8n.* We will assume a script is available (see Section 7).
4. **LLM Processing** – We use an LLM to find structured relations in the text. This involves a carefully designed prompt engineering setup with a `User Prompt` and a `System Prompt` to guide the model.

   - **Implementation**: n8n has a native **Basic LLM Chain** node. If using Google's Gemini API, there is no native node, so we use an **HTTP Request** node to call the API endpoint (e.g., `https://generativelanguage.googleapis.com/...`) or a custom code node with the `google-generativeai` Python library.

   - **User Prompt**: This is the prompt sent by the user (or n8n workflow) containing the specific text to be analyzed.
     ```
     You are an expert‑level financial‑domain NER and Relationship Extraction engine.

     ### Task
     Analyse the following text chunks **exclusively** from the *“Board of Directors”* section of {{ $json['Company Name'] }}， an SGX‑listed company’s annual report in {{ $json.Year }} and return **exactly one** JSON object with the schema described below.

     {{ $json.toJsonString() }}

     ### Output JSON schema
     {
       "reportYear"        : int,      // publication year (e.g. 1995, 2020, 2024)
       "entities"          : [         // all unique people & companies, there could be multiple companies as some people have director roles at different companies
         {
           "entityId"       : string,  // e.g. "PERSON_{canonicalName all capital letter}" or "COMPANY_{company name all capital letter}"
           "type"           : "Person" | "Company",
           "canonicalName"  : string,  // official full name
           "mentions"       : string[],// all surface forms (if is a person, should add all possible legal permutation of the canonicalName, you should also look up if he has another legal name in a different country, or know as a nickname.)
           "NER_Confidence" : float,   // 0‑1
           "source"         : int   // page, in format {page number, int, less than 999} e.g. 33
         },
         ...
       ],
       "relationships"     : [         // person → company role links (a person can be related to multiple companies and one person can have multiple relationships with one company) or person → person links (family)
         {
           "sourceEntityId" : string,  // person id
           "targetEntityId" : string,  // company id | person id (if family)
           "role"           : {
              "category"    : "Director" | "C‑Suite" | "Family | "Others", // coarse bucket
              "details"     : string                             // raw title (e.g. "Chief Executive Officer")
           },
           "effectiveDate"  : string|null, // YYYY‑MM‑DD, YYYY or null
           "RED_Confidence": float,        // 0‑1
           "source"        : int         // page, same format as above
         },
         ...
       ]
     }

     ### Rules
     1. **Return only the JSON.** No additional commentary.
     2. Use the same entityId for identical real‑world entities (deduplicate by name context).
     3. Normalise role synonyms (e.g. "CEO" == "Chief Executive Officer").
     4. Populate `source` with the PDF path & page where the mention appears (format: `PXX`).
     5. Confidence scores must be decimals between 0 and 1.
     6. If a date is missing, set `effectiveDate` to null.
     ```

   - **System Prompt**: This prompt sets the persona and high-level instructions for the LLM.
     ```md
     # SGX Board‑of‑Directors NER + Relationship Extraction Prompt
     ## Objective  Parse the *“Board of Directors”* section of a Singapore‑listed company’s annual‑report PDF and emit a single structured valid JSON object. No extra keys, no comments, no trailing text.  ---  ## Top‑level JSON schema  ```jsonc {   "reportYear": <int>,   "entities": [Entity …],   "relationships": [Relationship …] }

     ## Implementation reminders for the NER/RED engine  * Prefer explicit phrases: *“appointed as”, “joined the Board”, “ceased to be”* to set `effectiveDate`. * Assign **confidence** heuristically; e.g. 1.0 for exact regex capture on a single PDF page, lower for inferred matches. * If the report year cannot be found, fall back to the PDF filename year; flag confidence ≤ 0.5. * Output must be *machine‑parsable* JSON. No trailing commas.
     ```

   - **Example Output**: The LLM will return a JSON string based on the provided text. We then parse it into a JSON object (n8n can do this automatically).
    ```json
    [
        {
            "Company Name": "DBS GROUP HOLDINGS LTD",
            "Year": 2024,
            "Data": "835744_DBS%20Annual%20Report%202024.pdf",
            "original": {
                "reportYear": 2023,
                "entities": [
                    {
                        "entityId": "COMPANY_DBS_GROUP_HOLDINGS_LTD",
                        "type": "Company",
                        "canonicalName": "DBS Group Holdings Ltd",
                        "mentions": [
                            "DBS GROUP HOLDINGS LTD",
                            "DBS Group",
                            "DBS",
                            "the Company"
                        ]
                    },
                    {
                        "entityId": "PERSON_PETER_SEAH_LIM_HUAT",
                        "type": "Person",
                        "canonicalName": "Peter Seah Lim Huat",
                        "mentions": [
                            "Peter Seah Lim Huat",
                            "Peter Seah"
                        ]
                    }
                ],
                "relationships": [
                    {
                        "sourceEntityId": "PERSON_PETER_SEAH_LIM_HUAT",
                        "targetEntityId": "COMPANY_DBS_GROUP_HOLDINGS_LTD",
                        "role": {
                            "category": "Director",
                            "details": "Chairman"
                        }
                    }
                ]
            },
            "processed": {
                "reportYear": 2023,
                "companyInfo": {
                    "name": "DBS Group Holdings Ltd",
                    "entityId": "COMPANY_DBS_GROUP_HOLDINGS_LTD"
                },
                "executives": [
                    {
                        "name": "Peter Seah Lim Huat",
                        "role": "Chairman",
                        "category": "Director"
                    }
                ]
            },
            "isValid": true,
            "timestamp": "2025-07-10T03:23:57.454Z"
        }
    ]
    ```

   - **Error Handling**: Sometimes the LLM might produce invalid JSON if the text is tricky. The workflow should check for parse errors. In the MVP context, just be aware to verify the output.
5. **Data Handling** – The complex JSON structure shown above is the final output from the LLM extraction. No further transformation is required within the n8n workflow. The entire JSON object is saved to a file, and the `load_graph_v_5.py` script handles all the necessary parsing of the `original.entities` and `original.relationships` arrays before loading the data into Neo4j.
6. **Load into Neo4j** – This step uses the same robust Python script method as the MAS workflow.
   - After the LLM generates the structured JSON data, save it to a file (e.g., `/files/files/NER_RED/DBS_GROUP_HOLDINGS_LTD_2024_NER_RED.json`) using a **Read/Write Files from Disk** node.
   - Use an **Execute Command** node to run the `load_graph_v_5.py` script, passing the path to the JSON file as an argument. The script's `ingest_annual` function is specifically designed to handle this data.
   - The command would look like: `python /path/to/load_graph_v_5.py --annual_json /files/files/NER_RED/DBS_GROUP_HOLDINGS_LTD_2024_NER_RED.json`
   - The script handles the complex logic of deduplicating entities (Persons and Companies) and merging the relationships into Neo4j, ensuring data integrity.
   - Confirm insertion by checking for new relationships with `source = 'annual_report'` in Neo4j.
7. **Workflow activation**: Name the workflow “SGX Annual Reports to Neo4j”. Because annual reports are typically yearly, you might run this ad-hoc when new reports are available or on a schedule if you continuously monitor companies. In an MVP demo, you might just run it manually after adding a new PDF to the folder.

**Note**: This SGX workflow is the most complex due to its reliance on PDF parsing and LLM-based extraction. Our project repository contains two key scripts for this process:
- `sgx_ner_to_neo4j.py`: An early, self-contained script that handles the full pipeline for a single PDF—extracting text, calling an LLM for analysis, and loading the results into Neo4j.
- `load_graph_v_5.py`: The final, unified ingestion script. Its `ingest_annual` function is designed to load the structured JSON data that is the *output* of the LLM extraction process.

For a non-technical user, the process can be simplified to running a script that orchestrates this flow. To demonstrate n8n's role, we use an `Execute Command` node to run the Python script that loads the final JSON into Neo4j, as detailed in step 6 of the workflow.

### 5.3 Forbes & Wikidata Workflow (Wealth Anchors and Family Relations)

**Goal**: Seed the graph with known wealthy individuals (Forbes list) and expand the graph through family relationships via Wikidata.

**Data Sources**:
- **Forbes “Singapore’s 50 Richest”** list, which provides names of the top affluent people in Singapore. These serve as high-confidence UHNW anchors.
- **Wikidata**: A collaborative knowledge base that can provide structured data about those people, particularly family relations (spouse, children, parents) via properties like P26 (spouse), P40 (child) etc. Family ties can help identify clusters of wealth (e.g., a billionaire’s spouse or children might also be wealthy or become prospects).

**Workflow Outline**:
1. **Trigger** – Manual Trigger node to start.
2. **Forbes List Input** – We need the list of names of top 50 richest Singaporeans. Approaches:
   - If we have the data in a file (CSV or JSON) we can load it. For instance, maybe we saved “forbes_top50_sg2025.csv” with two columns: Rank, Name.
   - For simplicity, embed the list in a **Set** node or **Code** node. For example, use a Set node to create an item for each person with a field `name`. (Or copy-paste them into an array in a Code node and output items.)
   - Alternatively, one could scrape Forbes website via HTTP node. But that site might be dynamic or require parsing. Given a static list is small, manual input is fine for MVP.
3. **Fetch Wikidata QIDs** – Every person might have a Wikidata entry identified by a QID (Q-number). To get family info, we first need the QID for the person’s Wikidata entity.
   - Use an **HTTP Request** node to the Wikidata API or SPARQL endpoint. One easy method: use the **Wikidata search API**. For example, call:  
     `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=<Person Name>&language=en&format=json`  
     This returns search results with possible QIDs for that name.
   - Parse the JSON to get the top match QID (be careful with common names; ideally ensure you got the correct individual by some filter like description containing “Singapore” etc. – for MVP, assume top result is our person if name is distinctive).
   - You can use a Code node to pick the first result’s `id` field as QID.
   - Now add that QID to the item data (e.g., each item now has `{name: "Person Name", qid: "Qxxxx"}`).
4. **Fetch Family Relations from Wikidata** – Once we have QIDs:
   - We can use the **Wikidata API or SPARQL** to get specific properties. For simplicity, use the API again to get claims:
     For example, call:  
     `https://www.wikidata.org/wiki/Special:EntityData/<QID>.json`  
     This returns a JSON with all data for that entity. Within it, look at `claims` for P26 (spouse), P40 (child), P22 (father), P25 (mother). Each claim will have a value pointing to another QID (the related person).
   - Alternatively, use a SPARQL query via HTTP. For example, a single query could retrieve all family members in one go:
     ```sparql
     SELECT ?relation ?relName WHERE {
       wd:<QID> (wdt:P26|wdt:P40|wdt:P22|wdt:P25) ?rel .
       ?rel rdfs:label ?relName; wikibase:directClaim ?prop .
       FILTER(LANG(?relName) = "en")
       BIND(
         IF(?prop = wdt:P26, "spouse",
           IF(?prop = wdt:P40, "child",
             IF(?prop = wdt:P22, "parent",
               IF(?prop = wdt:P25, "parent", "other"))))
         AS ?relationType)
     }
     ```
     (This is more advanced; for MVP we can do multiple simpler calls.)
   - So, for each person (Forbes name):
     - Use HTTP node to get their Wikidata JSON.
     - Use a **Code** node to extract spouse/child/parent names from that JSON. The JSON provides QIDs of related persons; you then need to fetch their labels (names). Sometimes the initial JSON includes labels for linked entities under a `labels` section. If not, you might call another API to get those names.
     - The output we want: a set of relationships like PersonA -> PersonB with relation type.
     - For example, if “John Doe” has spouse Q123 and child Q456, we output:
       - `{ personA: "John Doe", personB: "Jane Doe", relation: "spouse", source: "Wikidata", url: "https://www.wikidata.org/wiki/Q123" }`
       - `{ personA: "John Doe", personB: "Johnny Doe Jr.", relation: "child", source: "Wikidata", url: "https://www.wikidata.org/wiki/Q456" }`
       (assuming Q123 was Jane, Q456 the child’s name).
     - Also note: we should treat parent (father/mother) both as relation "parent" for simplicity. And consider whether personA should always be the anchor person (the Forbes person). It might suffice to capture one direction; in Neo4j we’ll store as undirected or both ways as needed.
   - This part can be tricky, but even if we only manage spouse and maybe one relation for demonstration, it’s okay. The key is to show how external data enriches the graph.
5. **Load into Neo4j** – This step uses the same robust Python script method as the other workflows. The data gathered from Forbes and Wikidata should be compiled into a structured JSON file that the `load_graph_v_5.py` script can process.
   - After generating the JSON data, save it to a file (e.g., `/files/wikidata_family.json`) using a **Read/Write Files from Disk** node.
   - Use an **Execute Command** node to run the `load_graph_v_5.py` script, pointing to the JSON file. The script's `ingest_wikidata` function is built to handle this data, creating both the person nodes and the family relationships.
   - The command would look like: `python /path/to/load_graph_v_5.py --wikidata_json /files/wikidata_family.json`
   - This approach ensures that all data, including family relations, is processed through the same deduplication and ingestion pipeline, maintaining data consistency in Neo4j.

   For reference, the `ingest_wikidata` function in the Python script uses a `MERGE_FAMILY` query that is conceptually similar to the Cypher block below. The actual script uses internal IDs for more robust matching, but this illustrates the core logic:
   ```cypher
     UNWIND $rows AS r
     MERGE (a:Person {name: r.personA})
     MERGE (b:Person {name: r.personB})
     MERGE (a)-[rel:FAMILY]->(b)
     ON CREATE SET rel.relation = r.relation, rel.source = r.source, rel.url = r.url
     ON MATCH SET rel.relation = coalesce(r.relation, rel.relation),
                  rel.source  = coalesce(r.source, rel.source),
                  rel.url = coalesce(r.url, rel.url);
     ``` 
6. **Mark Forbes anchors (optional)**: We might also want to insert the Forbes persons themselves as nodes if not already, perhaps with a label or property indicating they are on the rich list (which could be a “source” tag as well). Since the family insertion already MERGEs the anchor person node, they’re in the graph. We could add a property like `anchor=true` or `source="Forbes2025"` on those Person nodes if needed for identification. This could be done via an extra Cypher or by including in one of the above (but not critical).
7. **Finalize**: Name this workflow “Forbes & Wikidata Enrichment”. Run it. It should quickly add those nodes and edges to Neo4j. Verify by querying Neo4j for any `FAMILY` relationships: `MATCH (p1:Person)-[f:FAMILY]->(p2:Person) RETURN p1.name, f.relation, p2.name`.

Now we have a knowledge graph in Neo4j populated from three pipelines:
- MAS: Person–Company roles (mostly finance sector executives).
- SGX: Person–Company roles (public company directors, etc.).
- Wikidata: Person–Person family relations (for known wealthy individuals).

Each part used n8n to orchestrate extraction and loading. Next, we consider the **scoring logic** that identifies UHNW prospects from this graph.

### 5.4 Scoring Workflow (Graph-Based UHNW Scoring)

**Goal**: Compute a “score” for each Person in the Neo4j graph that indicates how likely they are to be UHNW, using the network centrality and role-based signals in the graph.

**Context**: Our approach uses a custom, iterative, weighted PageRank algorithm to score every `Person` and `Company` in the graph. Since the Neo4j GDS (Graph Data Science) library is not available on the Aura Free tier, this entire logic is implemented in a single, multi-step Cypher script that is compatible with the APOC Core library.

The algorithm works as follows:
- **Base Scores**: It first calculates a `baseScore` for all nodes. For `Person` nodes, this is based on their `netWorth` and `roleScore`. For `Company` nodes, it's based on their `marketCap`.
- **Weighted Edges**: It assigns numerical weights to relationships. `HOLDS_POSITION` relationships are weighted by title (e.g., a `CEO` role is worth 5 points, a `Director` is 2), while `FAMILY` relationships have a standard weight.
- **Iterative Propagation**: The script then runs for a set number of iterations (e.g., 30), propagating scores between connected nodes according to the PageRank formula. This allows influence to flow through the network, so a person connected to high-scoring entities will see their own score increase.

**Scoring Implementation**:
The final implementation is a sophisticated, fault-tolerant Cypher script that can be run directly in the Neo4j Browser or executed via an n8n workflow. It is designed to be run as a single block.

**Workflow for scoring**:
1. **Trigger** – Manual or scheduled (ideally, this is run after any major data ingestion cycle).
2. **Compute Scores** – Use an **HTTP Request** node in n8n or run the script directly in the Neo4j Browser to calculate the scores. The script handles everything from initialization to the final iterative calculations.
   - The complete script is provided below. It should be executed as a single query. The parameters at the top (`alpha`, `beta`, `iterations`, etc.) can be adjusted to fine-tune the scoring behavior.

   ```cypher
      // ======================================
      //  Fault‑Tolerant Person‑Company PageRank
      //  — UHNW Discovery —
      //  Neo4j Aura Free compatible (APOC Core)
      //  Author: Li Yunfan
      // ======================================

      // === Parameter block ===
      :param alpha => 1;            // weight of log(netWorth)
      :param beta  => 1;            // weight of roleScore
      :param iterations => 30;      // max PR iterations
      :param damp => 0.85;          // PageRank damping factor d
      :param retain => 0.15;        // 1 - d, portion kept from baseScore
      :param lambda => 0.5;         // per-hop decay (3 hops ≈ λ^3)

      // === STEP 0. BaseScore with fault tolerance ===
      // Person
      MATCH (p:Person)
      WITH p, $alpha AS a, $beta AS b
      SET p.baseScore = CASE
      WHEN coalesce(log10(p.netWorth + 1),0)*a + coalesce(p.roleScore,0)*b < 0.1
      THEN 0.1
      ELSE coalesce(log10(p.netWorth + 1),0)*a + coalesce(p.roleScore,0)*b
      END
      ;
      // Company
      MATCH (c:Company)
      SET c.baseScore = CASE
      WHEN coalesce(log10(coalesce(c.marketCap,c.marketCapUSD,c.marketCapUSD_B*1e9,0)+1),0) < 0.1
      THEN 0.1
      ELSE coalesce(log10(coalesce(c.marketCap,c.marketCapUSD,c.marketCapUSD_B*1e9,0)+1),0)
      END
      ;
      // Reset scores & snapshot
      MATCH (n)
      SET n.score = n.baseScore,
      n.score_prev = n.baseScore
      ;

      // === STEP 1. Edge weight assignment ===
      WITH [
      ['ceo',5],
      ['group ceo',5],
      ['executive chairman',4],
      ['chairman',4],
      ['director',2],
      ['independent non-executive director',1],
      ['member, audit & risk committee',0.5],
      ['staff',0.1]
      ] AS kv
      WITH apoc.map.fromPairs(kv) AS roleWeights
      // Position → Company
      MATCH (p:Person)-[r:HOLDS_POSITION]->(c:Company)
      WITH r, roleWeights, toLower(trim(r.title)) AS titleKey
      SET  r.weight = coalesce(roleWeights[titleKey],1)
      ;
      // Family
      MATCH (p1:Person)-[r:FAMILY]->(p2:Person)
      SET  r.weight = 1.0
      ;

      // === STEP 2. Weighted out‑degree ===
      MATCH (n)-[r]-()
      WITH n, sum(coalesce(r.weight,1)) AS w
      SET  n.wOut = CASE WHEN w = 0 THEN 1 ELSE w END;

      // STEP 3. Iterative weighted PageRank (undirected)
      // ————————————————————————————————————————
      WITH $damp AS d, $retain AS g, $lambda AS l, $iterations AS iters
      UNWIND range(1,iters) AS iter
      CALL {
      WITH iter, d, g, l
      MATCH (src)-[rel]-(dst)
      WITH src, dst, rel, iter, d, g, l,
      CASE WHEN iter = 1 THEN rel.weight ELSE rel.weight * l END AS w
      WITH src, dst, (src.score / src.wOut) * w AS contrib, d, g
      WITH dst AS node, sum(contrib) AS gain, d, g
      SET node.score_prev = node.score,
      node.score      = g * node.baseScore + d * gain
      } IN TRANSACTIONS OF 20000 ROWS;

      // ————————————————————————————————————————
      // STEP 4. Convergence check
      // ————————————————————————————————————————
      MATCH (n)
      RETURN sum(abs(n.score - n.score_prev)) AS delta, $iterations AS iterations_run;
   ```
   - After execution, every `Person` node in the graph will have a `score` property reflecting their calculated importance.
3. **Retrieve Top Results** – We can optionally have n8n fetch the top-scoring persons and perhaps log or email them:
   - After setting scores, use another HTTP node with a Cypher like:
     `MATCH (p:Person) WHERE p.score IS NOT NULL RETURN p.name, p.score ORDER BY p.score DESC LIMIT 10`
   - The HTTP node will return data; we can use a Function to format it or simply log it. For MVP, you might just check in Neo4j Browser.
   - You’ll likely see known wealthy people (like those from Forbes list or CEOs of big companies) ranking high, which is expected – that’s how we flag potential UHNW leads.

4. **Use Scores** – The scores in Neo4j can now be used by RMs or an application. For example, a Relationship Manager’s dashboard could query for people above a certain score threshold to highlight as prospects. In our demo, we might not have the dashboard integrated, but RMs could use Neo4j Bloom or Browser to explore. We at least have a sorted list.

**Interpreting the scores**:
- Higher score = more indications of wealth (multiple senior roles, connections to known billionaires, etc.). 
- It’s a relative metric: if someone has score 5 and another 2, the first likely has more signals. There is no absolute meaning except as a ranking mechanism.
- In the final system, we documented that ~94% precision was achieved in identifying known HNW individuals, with a significant recall improvement – meaning the scoring method was effective compared to baseline. For handover, just know it’s a heuristic combining network centrality and known wealth connections.

### 5.5 Workflow Linking and Orchestration

You can run each workflow (MAS, SGX, Forbes/Wikidata, Scoring) individually. However, n8n also allows calling workflows from other workflows (via an “Execute Workflow” node). In a production scenario, you might create a master workflow that triggers all steps in order:
1. Run MAS ingestion.
2. Run SGX ingestion.
3. Run Forbes/Wikidata enrichment.
4. Run Scoring.
5. Notify or output results (maybe an email or dashboard update).

For MVP demonstration, running them one by one manually is fine. If you want to automate end-to-end on a schedule, you could use one workflow with multiple **Execute Workflow** nodes in sequence or simply schedule them around the same time.

Now that the workflows are set up, let’s cover how to configure Neo4j and verify the data.

## 6. Setting up Neo4j Aura Free and Connecting to the Graph

We chose **Neo4j AuraDB Free** for the knowledge graph database. Aura Free is a cloud-hosted Neo4j database with constraints (like smaller capacity and no Graph Data Science plugin) but it’s sufficient for an MVP and easy to share access.

### 6.1 Create a Neo4j Aura Free Instance

1. **Sign Up**: If you haven’t, go to the Neo4j Aura page and create an account. Use your work email if appropriate. Verify any email confirmation.
2. **Create Instance**: Once in the Aura console, click **“Create Free Instance”** (there’s usually a big button or card for this). You will be prompted to choose a name for your database, and possibly a region (choose one close to you for performance, e.g., Asia/Singapore region if available).
3. **Credentials**: When the database is created, Aura will show you the connection credentials:
   - **Neo4j URI** – It will look like `neo4j+s://<randomid>.databases.neo4j.io` (the `neo4j+s://` means it’s a secure Bolt protocol).
   - **Username** – default is `neo4j`.
   - **Password** – Aura auto-generates a password. **Copy this password** and store it in a secure place. Aura might only show it once (you can reset it later if lost). You can also click to download a `.txt` with the credentials.
4. **Neo4j Browser**: Click the option to **"Open in Browser"** or go to https://browser.neo4j.io/ and enter your URI, user, password. This opens Neo4j’s web interface for running queries (Neo4j Browser). It’s a convenient way to inspect the DB.
5. **Connection Test**: In Neo4j Browser, run a test query:
   ```
   RETURN "Hello Neo4j!" AS test
   ```
   This should return a table with “Hello Neo4j!”. If you see an error or can’t connect:
   - Check that your internet connection allows WebSockets (Aura uses the Bolt protocol over port 7687; most networks allow it as it’s TLS encrypted on standard ports).
   - If it fails, you can also try the Neo4j **Bloom** UI or Neo4j Desktop (but Browser is simplest).
   - Ensure you used the correct credentials.

At this point, you have an empty database ready to receive data from our workflows.

### 6.2 Configure Neo4j Connection in Workflows

We already added a Basic Auth credential in n8n for Neo4j (Section 4). Now, in each HTTP Request node that contacts Neo4j:
- Set the URL. Aura doesn’t expose a direct HTTP transaction endpoint by default for free tier, but it does have a new **Aura Query HTTP API**. The exact URL for that might be something like `https://<dbid>.databases.neo4j.io:7687` with a specific route. (In our project, we primarily used the Bolt protocol via code, not the HTTP API.)
- Simpler: We can use Neo4j Browser or client for initial data load if needed, but let’s assume we try via n8n:
   - Some have used the route: `https://<dbid>.databases.neo4j.io/db/<dbname>/tx` but this may require Aura professional. Instead, an alternative:
   - Use a tool like **Pipedream** or a custom node (beyond our scope).
- **Recommendation**: Given potential complexity, you may run the Cypher manually in Neo4j Browser to verify, then possibly skip n8n for the actual load if stuck. For handover, ensure the next person knows the Cypher to load data.

For example, to manually run the MAS data insert, open Neo4j Browser and run:
```cypher
MERGE (p:Person {name: "Wong Kim Seng"})
MERGE (c:Company {name: "United Overseas Bank Limited"})
MERGE (p)-[:HAS_ROLE_AT {role:"Chairman", source:"MAS", as_of:"2025-07-01"}]->(c);
```
(as a sample). But of course, doing this for each entry is tedious; the workflows or scripts are meant to batch it.

**Important Neo4j Settings**:
- We created unique constraints on Person and Company name to avoid duplicates. It’s good to set these in Neo4j Browser now:
  ```cypher
  CREATE CONSTRAINT person_name_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE;
  CREATE CONSTRAINT company_name_unique IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE;
  ```
  This ensures that `MERGE` on name behaves as intended (no two Person nodes with same name). We rely on our input being clean; the constraint will throw an error if a duplicate name is attempted with different casing or spacing, but our normalization steps aim to prevent that.
- Aura Free has a size limit (roughly 50k nodes and relationships). Our MVP data volume is way below that (likely a few thousand at most), so we’re fine.

### 6.3 Browser Visualization

To help non-technical colleagues explore the graph:
- **Neo4j Browser**: Allows running queries and visualizing small graph results. For instance:
  ```cypher
  MATCH path=(p:Person)-[:HAS_ROLE_AT]->(c:Company) RETURN path LIMIT 50;
  ```
  will show person-company connections. You can click on nodes and relationships to see properties (e.g., role, source).
- **Neo4j Bloom (TODO)**: Aura comes with Bloom, a visual exploration tool (the Aura console might have a “Open in Bloom” button). Bloom provides a search-like interface (e.g., type a person’s name to see their neighborhood). We used Bloom in development to confirm that the entity resolution was working – e.g., all references to the same company merge into one node. Bloom is more user-friendly for analysts.
- For our MVP handover, demonstrating a query in Browser or Bloom to show the final output is useful. For example, show how a person identified as a top prospect is connected to various companies or an anchor family, explaining why they got a high score (the “Reason to Flag” concept).

## 7. Deploying Python Crawlers and Scripts (MAS, SGX, Wikidata)

While n8n orchestrates the high-level workflow, many of the heavy-lifting tasks (like PDF parsing, calling LLM, complex data cleaning) were implemented in Python during development. We include these **Python-based crawlers and pipeline scripts** as part of the handover so that you have an alternative way to run the data ingestion or debug issues.

### 7.1 Setting up the Python Environment

**Install Python**: Ensure Python 3.x (preferably 3.9 or above) is installed on your Windows machine if you plan to run the scripts outside of Docker. You can get it from the Microsoft Store or Python.org installer. Make sure `python` and `pip` are on your PATH.

**Project Code**: Obtain the project code repository (it might be on GitHub or shared folder). The repository is named “Knowledge Graph for UHNW Spotting” and contains subfolders for each data source and the Neo4j integration. Copy this to your local drive (e.g., `C:\UHNW_Project\`).

**Python Dependencies**: The repository includes requirements files. Open a terminal (Command Prompt or PowerShell) and navigate to the project directory. Run:
```bash
pip install -r requirements.txt
``` 
(if there are multiple, install the main one or each subfolder’s as needed). Key packages include:
- **neo4j & py2neo** – Neo4j database drivers.
- **pandas, numpy** – data handling.
- **pdfplumber, PyPDF2** – PDF text extraction for SGX.
- **spacy** (possibly, if we used it for NER fallback).
- **google-generativeai** – to call the Google PaLM API for LLM NER.
- **rapidfuzz** (and/or `thefuzz`) – for fuzzy matching in entity deduplication.

*(If any package fails to install on Windows, you may need build tools or to find an alternative. For instance, PyPDF2 is pure Python (should be fine), pdfplumber might need `pip install pdfplumber` which includes PDFMiner as dependency.)*

**Environment Variables**: Create a `.env` file in the project root (or you can set system environment variables). According to our docs, the `.env` should contain:
```ini
NEO4J_URI=neo4j+s://<your-db-id>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-password>

GOOGLE_API_KEY=<your-PaLM-API-key>  # if using Google LLM
PDF_PATH=<path-to-an-annual-report.pdf>  # optional, used by some scripts for input
``` 
Replace values accordingly. The Python scripts will read this .env for config.

*(Storing credentials in .env is fine for development, but ensure this file is not shared publicly. In operations, consider more secure vaults.)*

### 7.2 Running Individual Scripts

The UHNW pipeline is composed of several standalone Python scripts and notebooks, each responsible for a specific stage of data acquisition, processing, or loading. Below is a detailed breakdown of each key script and its role in the system.

#### Data Acquisition & Ranking Scripts (`Ranking/`)

These scripts are responsible for fetching data from external, public sources of wealth information like Forbes and Bloomberg.

*   **`Ranking/Forbes/forbes_billionaires_scraper.py`**
    *   **Purpose**: A web scraper designed to fetch the complete Forbes World's Billionaires list for a given year.
    *   **Functionality**: It queries the public-facing Forbes JSON API to retrieve all pages of the list (approx. 3,000 records). It includes a robust fallback mechanism: it first attempts to use the `pyforbes` library, and if that fails, it uses a raw `requests`-based scraper. The script includes throttling to prevent overwhelming the API.
    *   **Output**: A CSV file (e.g., `forbes_billionaires_2024.csv`) containing details for each billionaire, including rank, name, net worth, country, age, and industry.

*   **`Ranking/Bloomberg/sync_billionaires.py`**
    *   **Purpose**: To synchronize wealth data from a Bloomberg-sourced CSV file directly into the Neo4j database.
    *   **Functionality**: This script reads a `bloomberg_billionaires.csv` file and performs an "upsert" operation into Neo4j. For each person in the CSV, it uses a `MERGE` query to either create a new `:Person` node or update an existing one based on their name. It intelligently parses net worth strings (e.g., "$5.2B") into integers and updates properties like `netWorth`, `country`, and `industry`. The process is batched for efficiency.
    *   **Input**: `bloomberg_billionaires.csv`.

#### MAS Data Processing (`MAS/`)

*   **`MAS/MAS_ORG_NER.ipynb`**
    *   **Purpose**: A two-part Jupyter Notebook for processing and loading data from the Monetary Authority of Singapore (MAS).
    *   **Functionality**:
        1.  **Organizational Data**: The first part (`AuraUploader`) parses `MAS_FID_*.csv` to build a foundational graph of financial institutions, their sectors, licenses, and business activities in Neo4j.
        2.  **Personnel Data**: The second part (`DateTimeVersionedUploader`) ingests `MAS_Personnel.csv`. It uses fuzzy matching to link individuals to the correct organizations and creates `:HAS_OFFICER` relationships. Crucially, it adds a `last_updated_run` timestamp to each relationship for data versioning.
    *   **Output**: Enriches the Neo4j graph with nodes for Singapore's financial institutions and the key personnel who run them.

#### SGX Annual Report Pipeline (`SGX Annual Reports/`)

This collection of scripts and notebooks is focused on extracting data from unstructured PDF annual reports.

*   **`SGX Annual Reports/FIN_ner_red_neo4j_pipeline.ipynb`**
    *   **Purpose**: This is the primary, state-of-the-art pipeline for processing a single annual report. It leverages the Google Gemini 1.5 Pro LLM for high-accuracy NER and relationship extraction.
    *   **Method**:
        1.  **TOC Analysis**: Uses `pdfplumber` to extract the Table of Contents.
        2.  **Section Identification**: Locates the starting page of the "Board of Directors" or equivalent section from the TOC.
        3.  **Targeted Extraction**: Extracts text page-by-page starting from the identified page until a concluding keyword (like "Corporate Governance") is found.
        4.  **LLM Processing**: Sends the extracted text to the Gemini LLM to get a structured JSON output of `:Person`, `:Organization`, and `:ROLE` relationships.
        5.  **Neo4j Ingestion**: Loads the structured data into the Neo4j database.
    *   **Usage**: Set the `PDF_PATH`, `GOOGLE_API_KEY`, and Neo4j credentials as environment variables and run the notebook cells sequentially.

*   **`SGX Annual Reports/Case Study/Venture Corporation Limited/ExtractTOCExtractDirectorPages.ipynb` & `parallel_pdf_processor.py`**
    *   **Purpose**: A notebook and script combination designed for **batch processing** thousands of PDFs to extract only the pages relevant to the board of directors.
    *   **Method**: The notebook (`ExtractTOCExtractDirectorPages.ipynb`) acts as a controller, invoking the `parallel_pdf_processor.py` script on a directory of PDFs. The script then:
        1.  **Processes PDFs in parallel** for high throughput.
        2.  **Finds candidate pages** by searching for keywords (e.g., "board of directors") in both PDF bookmarks and the full text using `pypdf`.
        3.  **Filters content** using `spaCy` and heuristic rules (like "personnel density") to validate that the pages contain relevant director information.
        4.  **Saves the filtered text** into a `_extracted.json` file for each PDF, ready for downstream processing.

*   **`SGX Annual Reports/sgx_ner_pipeline_notebook.ipynb`**
    *   **Purpose**: An alternative, non-LLM pipeline for NER and relationship extraction from a single PDF.
    *   **Method**:
        1.  **Full Text Extraction**: Uses `pdfminer.six` to extract the entire text content of the PDF.
        2.  **Rule-Based NER**: Applies `spaCy` with custom rules to identify `:Person` and `:Organization` entities and infer relationships.
    *   **Usage**: This can be used as a fallback or for comparison when an LLM is not available. It produces CSV files of the extracted entities and relationships.

*   **`SGX Annual Reports/sgx_ner_to_neo4j.py`**
    *   **Purpose**: An end-to-end, self-contained pipeline for extracting relationship data from a single PDF annual report.
    *   **Functionality**: This script orchestrates the entire process for one PDF: (1) It extracts raw text using `pdfplumber`. (2) It splits the text into manageable chunks. (3) It sends each chunk to the Google Gemini LLM with a carefully engineered prompt to perform Named Entity Recognition (NER) and Relationship Extraction (RE), outputting a structured JSON. (4) It loads this JSON data into Neo4j using `py2neo`, creating `:Person` and `:Company` nodes and `:HAS_ROLE_AT` relationships.
    *   **Usage**: Primarily for testing or processing single, high-value reports. The logic from this script forms the basis of the larger, orchestrated n8n workflow.

#### Unified Data Loading & Deduplication (`Neo4j/`)

These scripts are the core of the data consolidation and cleaning process.

*   **`Neo4j/load_graph_v_5.py`**
    *   **Purpose**: This is the **primary, unified ingestion script** for the entire project. It is designed to be the single point of entry for loading data from all sources into Neo4j while ensuring data consistency.
    *   **Functionality**: It maintains an in-memory registry of all persons and companies. When loading new data (from MAS, SGX, or Wikidata), it uses this registry and fuzzy matching (`rapidfuzz`) to deduplicate entities in real-time. For example, if it encounters "Peter Seah" and "Peter Seah Lim Huat," it can merge them into a single entity with an alias. It contains dedicated functions to ingest different data formats (`ingest_annual`, `ingest_wikidata`, `ingest_mas`) and uses idempotent `MERGE` queries to safely write to Neo4j.
    *   **Usage**: This script is called by n8n workflows after they have prepared the source data files (e.g., the JSON from the SGX LLM pipeline).

*   **`Neo4j/batch_dedup.py`**
    *   **Purpose**: A post-processing script for performing large-scale, batch deduplication on `:Person` nodes already in the database.
    *   **Functionality**: It addresses duplicates that may have been missed by the real-time checks in `load_graph_v_5.py`. The script (1) exports all person names from Neo4j, (2) uses fuzzy matching and a graph-based clustering algorithm (`networkx`) to find groups of similar names, (3) creates a canonical `:CanonicalPerson` node for each cluster, and (4) links all the duplicate `:Person` nodes to this new canonical node via a `:SAME_AS` relationship. This creates a "golden record" for each individual without deleting original data.
    *   **Usage**: Should be run periodically as a data maintenance task to ensure the graph remains clean and accurate.

     - Post-process the LLM output (ensure JSON structure, etc.).
     - Use Neo4j Python driver to MERGE the nodes and relationships into the graph (essentially the same Cypher logic we described earlier, executed via the driver).
     - Print or log what it inserted.
- **`load_graph_v_5.py`** (in `Neo4j/` directory): This appears to be a **unified loader script** that might combine all sources and handle deduplication. Running `python Neo4j/load_graph_v_5.py` would likely:
  - Read data from various intermediate outputs or directly call sub-scripts for MAS, SGX, Forbes, etc.
  - Apply **deduplication**: e.g., if the same person is found in MAS and SGX, ensure one node. It uses fuzzy matching to avoid duplicates (like “Robert Wong” vs “Robert Wong Jr.” etc.).
  - Ensure no self-loops or redundant relationships are created.
  - This might be the one-stop script to rebuild the graph from scratch with all data. It’s handy for a full refresh.
- **`batch_dedup.py`** (Neo4j/): might contain helper functions to merge duplicate nodes or clean up naming variations. You typically won’t run this standalone unless you need to re-run dedup steps.
- **`process_wd_full_clean_v6.py`** (in `WikiData/Data/`): This is the core ETL script for processing Wikidata query results. It reads raw JSON data, cleans it, resolves relationship conflicts (e.g., a person being both father and mother to someone), and structures the data into a clean `data.json` file containing person nodes and family relationship edges for loading into Neo4j.
<!-- - **`mark_local_files.py`** (in `SGX Annual Reports/`, optional): A utility script to cross-reference a tracking CSV (like `FilesTrack.csv`) with a directory of downloaded annual reports. It adds a flag to the CSV indicating whether each report file actually exists locally, which is useful for managing the data collection process. -->

**Running a full pipeline**: For initial handover, the straightforward path:
- Run the MAS routine:
  - If no single script, you can run the notebook or incorporate MAS into `load_graph_v_5.py`. Let’s assume the unified loader covers it. If not, possibly the unified loader expects MAS data prepared as CSV or JSON in a folder.
- Run the SGX script for each PDF of interest (or modify it to loop through a directory of PDFs).
- Run the Forbes/Wikidata process:
  - Possibly a script in Ranking or included in unified loader as well.
- The unified loader might call the above or load intermediate files:
  - e.g., maybe we first produce `mas_output.json`, `DBS_GROUP_HOLDINGS_LTD_2024_NER_RED.json`, `family_output.json` and then the loader merges them.

If the documentation is unclear, an easier route:
Use n8n for MAS & Wikidata (since those we did in workflow), and use Python for SGX. This hybrid approach is fine.

Finally, ensure the Neo4j DB has all data loaded. You can re-run `load_graph_v_5.py` to double-check (it might also do consistency checks).

### 7.3 Triggering Python Scripts from n8n (Optional)

If you prefer everything to be run via a single interface (n8n), you can trigger these Python scripts from n8n:

- **Execute Command Node**: As noted, this runs a shell command inside the container. If we customize our n8n Docker image to include Python and our project files, we could run something like:
  ```bash
  python /data/SGX\ Annual\ Reports/sgx_ner_to_neo4j.py
  ```
  inside the container. However, our default n8n image doesn’t have Python. You’d have to build a custom image or use an SSH node to trigger on host.
- **SSH Node**: Another trick is to run an SSH server on the host and have n8n SSH into localhost to run the script on Windows. This is probably more trouble than it’s worth for MVP.
- **Webhooks/Manual**: It might be acceptable that for the SGX part, the team runs a script manually when needed (since adding a new annual report is not daily work).
- **Integration**: For a more automated approach without messing with the n8n image, consider containerizing the SGX pipeline separately (a small Python container that does the job on a trigger), or use a cloud function. These are beyond MVP scope.

In summary, the Python tools are there to complement n8n:
- Use them for tasks that n8n can’t easily do (PDF parsing, heavy data massaging).
- They also serve as documentation of the logic (e.g., how deduplication works).
- For handover, ensure the team has access to the code and knows how to run these scripts. Include sample commands in a README (e.g., “To load all data from scratch, run `python Neo4j/load_graph_v_5.py`”).

## 8. Triggering Crawlers from n8n

As partially discussed, n8n triggers can kick off data collection jobs:

- **Scheduled runs**: You can use the **Cron node** in each workflow to schedule periodic data refresh. For example, set MAS workflow Cron to run weekly (to catch any org chart changes), SGX to run quarterly (around earnings season when new reports come), and Forbes/Wikidata to run annually (Forbes list updates yearly).
- **On-Demand**: Manual Trigger is fine for now. If an RM or user wants fresh data, they open n8n and execute the workflows.
- **Chaining**: If one part depends on another (not really, they are independent sources), you could chain them as described in 5.5.
- **Real-time triggers**: This MVP isn’t fully real-time, but n8n could listen to events (webhooks) – e.g., if integrated with a website form, an event could trigger a search for that person in the graph. That’s future scope.

For now, typical use might be:
   1. Run all ingestion workflows in the morning.
   2. Then run the scoring workflow.
   3. Check results and provide to RMs (maybe by exporting a list or screenshotting top leads).

Make sure to monitor the n8n execution list for any failures. If a workflow fails halfway (e.g., one broken HTML parse), it might stop – in such a case, fix the issue or rerun.

## 9. LLM-based NER and Relation Extraction Pipeline

This deserves a summary as it’s a unique part of the system.

**What it is**: Using a Large Language Model to read unstructured text and output structured data (entities and relations). We applied this to the SGX annual report text primarily, but the concept can extend to news articles, etc.

**Model Setup**: We used ***Google’s Gemini 2.5 Flash*** model via their API. The advantage was its strong understanding of text and we could keep data within our controlled prompt. Alternatively, OpenAI’s GPT-4 could do similarly.

- If using Google: you must have set the `GOOGLE_API_KEY` env var. This key is obtained from Google Cloud’s Generative Language API setup (you enable the API and create an API key in GCP). The Python library `google-generativeai` uses it when you call, e.g., `generate_text(model='XXX', prompt=...)`.
- The prompt we used was likely carefully crafted to produce JSON output of the desired schema. If you open the `sgx_ner_pipeline_notebook.ipynb` you might find the exact prompt template used.
- If using OpenAI: you’d set the OpenAI API key similarly, and perhaps use n8n’s node or openai library in Python.

**Prompt Template in 5.2**

**Ensuring reliability**: We enforced the JSON schema by either:
- Post-processing the LLM output (if it gave slight deviations, we corrected via regex or a second pass).
- Using smaller chunks if text is large (we isolated just the relevant section for the LLM to avoid confusion and cost).
- Validating the JSON (the code ensures keys exist and are not empty).

For a non-technical colleague, the main thing is: the AI is reading text and finding names/relationships so we don’t have to write complex parsers. If it errors out, check:
   - Prompt might need tweaking.
   - The API key might have run out quota or internet issue.
   - The text might be unusual (e.g., scanned PDF or image – our method won’t work on image-based PDFs unless OCR is applied first).

If the LLM approach fails, a backup could be using rule-based extraction or manual review, but that’s not ideal. Our results were quite good with the chosen model.

**Cost**: Using LLM APIs may incur cost. For MVP scale (a few documents), this is negligible – a few cents. Just be mindful if scaling up, and monitor API usage on your account.

## 10. Inserting Nodes and Relationships into Neo4j (Data Model & Cypher)

We have mentioned the schema but let’s clearly define it and show some Cypher:

**Graph Schema**:
- **Person (Node)**: Represents an individual. Key property: `name` (unique). We may also have properties like `score` (for results), and possibly an `anchor` flag or other tags in future.
- **Company (Node)**: Represents an organization (company, bank, etc.). Key property: `name` (unique). Could also have properties like `type` (if we categorize or note if it’s listed etc., not in MVP).
- **Relationships**:
  - `(:Person)-[:HAS_ROLE_AT {role, source, url, as_of}]->(:Company)`. This denotes a person holds a role/position at a company. We use a single relation type for all kinds of roles (director, CEO, etc.) as indicated by the `role` property. 
    - Example: `(:Person {name:"Alice"})-[:HAS_ROLE_AT {role:"CEO", source:"MAS", as_of:"2025-07-01"}]->(:Company {name:"DBS Bank Limited"})`.
  - `(:Person)-[:FAMILY {relation, source, url, as_of}]->(:Person)`. This denotes a family relation between two people. We treat it as directed for storage, but essentially it’s undirected logically (if A is parent of B, B will have A as parent too, or one could add the inverse relation; our system for simplicity may only add one direction).
    - `relation` can be “spouse”, “parent”, or “child” (we consider father/mother just as parent).
    - Example: `(:Person {name:"Charlie"})-[:FAMILY {relation:"spouse", source:"Wikidata"}]->(:Person {name:"Diana"})`.
- We didn’t explicitly model a separate node type for *Sector* or *Activity* in this MVP, though the MAS data had sectors. We decided to focus on person and company only (the CLAUDE.md shows Sector, Activity, Licence nodes possibly planned, but not critical for MVP unless needed for future analysis).


But it can duplicate spouses (two directions). Up to you; not doing it is fine as long as queries are done undirected.

**Checking Data**: After ingestion, you can run:
- Count nodes: `MATCH (p:Person) RETURN count(p)` (how many persons).
- See a sample: `MATCH (p:Person)-[r:HAS_ROLE_AT]->(c:Company) RETURN p.name, r.role, c.name LIMIT 10`.
- Check an anchor’s family: `MATCH (p:Person {name:"Robert & Philip Ng"})-[:FAMILY]->(q) RETURN p.name, q.name, labels(q)`. (The Ng brothers likely appear if we included them, for example.)

Our design includes **provenance**: every relationship has a `source` and `url` so we know where it came from. This is important for trust and updates. For instance, if tomorrow MAS updates a director name, we can trace which data came from MAS and update accordingly.

**Neo4j Browser tip**: You can visualize a subgraph by searching: in Neo4j Browser's search bar, type a company name or person name to get a node, then click “Expand” on it to see connected nodes. This is useful for exploring.

## 11. Reading & Interpreting UHNW Output Scores

After running the scoring (Section 5.4), each Person node in Neo4j will have a `score` property (numeric). How to interpret:

- **High score**: Indicates strong signals of wealth. For example, someone who is CEO of a major bank and appears on a rich list will score high due to multiple roles and anchor connections.
- **Low score**: Likely a person with maybe one minor role or no significant connections in our data.
- **Threshold**: You might choose a threshold to classify UHNW “prospect”. If the top scores range, e.g., from 5 down to 1, you might say anything 3 and above is noteworthy. This threshold can be tuned.
- **Relative ranking**: The most useful aspect is sorting prospects by score so RMs can focus on the top few. The exact value is less important than the rank order.

To get the top prospects:
```cypher
MATCH (p:Person)
WHERE p.score IS NOT NULL
RETURN p.name, p.score
ORDER BY p.score DESC
LIMIT 20;
```
This yields a list of names with scores. Likely you’ll recognize some names (maybe known tycoons or prominent executives) there. These would be your UHNW leads.

For each high scoring individual, you can investigate *why* their score is high by looking at their connections:
- Run `MATCH (p:Person {name:"XYZ"})-[r]-(x) RETURN p, r, x` to see their immediate relationships. Maybe person XYZ is connected to Company ABC as CEO and is spouse of a billionaire – that explains the score.
- Our system was designed to provide a “Reason to Flag” which could be derived from the presence of certain connections (like “CEO of a public company (ABC Corp with market cap X)” or “Family member of [Billionaire]”). We haven’t automated the explanation in this MVP, but a quick look at the graph around the person can allow an analyst to articulate the reason.

In practice, the **RM dashboard** (if it existed) would highlight these reasons so RMs know why the system thinks this person is worth contacting. For now, the user (our colleague) may need to manually check the graph for context:
- Example: *Person A* has score 5 – looking at Person A’s relationships, we see:
  - A is a Board Member at Company X (which is a known large company).
  - A is also Board Chair at Company Y.
  - A is the child of Person B, who is on the Forbes list.
  So an RM could infer Person A is likely wealthy via inheritance and connections.

Encourage the team to use Neo4j Bloom for a more visual read: it can show a “mini-map” of how a person is connected to others. This often surfaces the non-obvious links.

To verify the scoring algorithm’s effect, one could test on known individuals:
- If someone known to be UHNW (from Forbes list) isn’t scoring top, maybe we need to adjust weights or data.
- If random lower-level folks are scoring high erroneously, check if data is wrong (e.g., a duplicate name mixing two people’s connections).
- Those checks were part of our model evaluation with precision/recall etc., but for handover, just ensure the output makes intuitive sense.

## 12. Common Bugs, Errors, and Fixes

During development and testing, we encountered some typical issues. Here’s a list of common problems and how to address them:

- **n8n Container Out of Memory**: If n8n crashes or the workflow execution hangs when processing large data (especially the SGX PDF/LLM node which could consume a lot of memory), it could be due to container memory limits. By default, Docker might allow using all available memory, but on Windows, WSL2 might have a limit. 
  - *Symptoms*: n8n UI stops responding, or execution log stops mid-run, possibly Docker shows container exited or restarting.
  - *Fixes*: Increase memory in Docker Desktop settings (e.g., allocate 4GB or more to Docker). Alternatively, break the task into smaller parts – for instance, process one PDF at a time rather than many, and perhaps offload heavy operations to an external script.
  - We implemented chunking for Neo4j insert to avoid huge transactions. If you see Neo4j transaction timeouts or memory issues, consider splitting the data into batches (e.g., 100 rows per Cypher execution). Aura Free might have limits on transaction size.
- **Docker Networking**: If n8n nodes cannot reach external services:
  - Check that your internet is accessible within the container. The container uses the host network/NAT, which normally is fine. But if your organization uses a proxy, the container might need proxy environment variables.
  - For Neo4j Aura specifically, ensure port 7687 is not blocked. If the HTTP API approach fails, use the Python driver (Bolt) as it’s designed to work with Aura’s encrypted Bolt out of the box.
  - If you can’t use Aura due to network, an alternative is Neo4j Desktop (local DB) – but then colleagues would need to install Neo4j locally and share the DB file, which is not as convenient. Try to get Aura working.
- **Crawler Throttling & Blocks**: When scraping MAS or other websites:
  - MAS directory is not heavy traffic, but if one were to scrape 1000 institutions quickly, MAS might temporarily block or your IP could be flagged. We added small delays and limited concurrency (in n8n, the default HTTP nodes are sequential anyway, not parallel, so that helps).
  - If you do need to scrape many pages, consider adding a 1-2 second Wait inside the loop. It will slow the run but be gentler on the server.
  - If scraping third-party sites, always respect robots.txt and any usage policies.
- **Data Quality Issues**: Some specific cases:
  - Person names like initials or with honorifics (Dr., Mr., etc.) – we stripped common titles (“Mr”, “Ms”) to normalize names. If you see duplicates like “Dr John Tan” and “John Tan” as separate nodes, it means our normalization missed “Dr.” – you can merge them or add that rule.
  - Company naming variations – e.g., “ABC Ltd” vs “ABC Limited”. We attempted to unify those (replaced " Ltd." with " Limited"). If new variations appear, update the normalization logic (either in code or manually merge in Neo4j).
  - Very common names – our rule was if a name is common (and if no company context, skip merging). This was to avoid merging two different people named “David Lee”. So you might find multiple Person nodes "David Lee" if they came from different sources without clear distinguishing info. This is intended to avoid false merges. Over time, a data steward might need to manually resolve if they are actually the same (maybe by cross-checking other attributes).
- **n8n Execution Issues**:
  - If a workflow is failing mid-way, check the n8n **Execution list** (in Editor UI, menu -> Executions) for error details. A common error could be “Function not found” if a node is misconfigured, or a credentials issue.
  - If an HTTP node to Neo4j returns unauthorized (401) – recheck the Basic Auth credential (password correct?) or if using the wrong endpoint.
  - If an HTTP node returns an error JSON from Neo4j, read it – often it will tell you if your Cypher syntax is wrong.
  - If the LLM node times out or fails, maybe the response was too large. Possibly break the text into two parts (if the board section is huge).
- **Docker Volume Persistence**:
  - Ensure the Docker volume is used so that workflows are saved. If you accidentally ran n8n without volume and created workflows, they would disappear when container restarts. The volume `n8n_data` prevents that. If something weird happens (like you lost workflows), check if you ran with `--rm` without a volume. To recover, you’d have to re-import workflows or recreate them.
- **Python Library Issues**:
  - If `google-generativeai` fails, ensure you have enabled the PaLM API in your Google Cloud project and the API key is valid. Test outside n8n by a short Python snippet.
  - If `neo4j` Python driver can’t connect, it might be a TLS issue or routing. Make sure you use `neo4j+s://` URI and the port default (Aura uses 7687 but the `+s` scheme covers that). The driver should be >= version 5 to match Neo4j 5.
  - Fuzzy matching (rapidfuzz): it’s used to auto-merge similar names. If it’s merging things it shouldn’t, you may need to adjust the threshold. We set a default ~93% similarity threshold – pretty high to avoid false merges. You likely won’t tweak this in MVP unless an obvious issue arises.

- **Catching up after downtime**: If the system hasn’t run in a while, some data might be stale (e.g., MAS might have new entries). It’s a good practice whenever you restart the system to run all ingestion workflows to refresh the graph.

## 13. Security and Data Privacy Considerations

This system deals with personal data (names of individuals, possibly their roles, wealth indicators). Even though the data is sourced from public records, when aggregated and processed it still should be handled carefully under privacy regulations (e.g., Singapore’s PDPA, or internal guidelines).

Key considerations:

- **Data Privacy (DPIA)**: A Data Protection Impact Assessment should have been conducted. The DPIA would note that all personal data in the system is from publicly available sources and used for a purpose (prospect identification) that is likely covered under business interest, but we must ensure:
  - We **do not store excessive personal details** beyond what’s needed (we store basically name and relationships, which is minimal).
  - Access to the data is limited to those who need it (RMs, relevant teams). In our MVP, it’s just within this local setup. In a deployed scenario, we’d implement access control.
  - **Consent/PDPA**: Since data is public, consent is not required from individuals for collection, but if used to make decisions, we should be transparent internally about data sources to avoid any compliance issues.
- **Credentials Security**: Keep API keys (Neo4j, LLM) secure. We used .env files and n8n credentials for this. Do not expose them in screenshots or share them widely. In documentation or code, they should be placeholders (as we’ve done).
- **Neo4j Aura Security**: The connection is encrypted (`neo4j+s` means Neo4j with TLS). Aura Free’s instance is protected by the credentials. Do not share the Neo4j password beyond the team. If someone new needs access, either share through a secure channel or add them via Aura’s user management (if available in free tier).
- **Network Security**: Because everything is on the local machine, ensure the machine is secure (login password, up-to-date anti-malware, etc.). If you run n8n without auth, anyone who can connect to your machine on port 5678 could potentially access it – so only run it in a trusted network (or enable the auth as shown).
- **Data at Rest**: The Neo4j data is in the cloud (Aura). Aura is a managed service by Neo4j – data is encrypted at rest and in transit by their design. For local backups, if you dump data to CSV or have intermediate files (like PDF or extracted JSON), treat them as confidential. When disposing of them or transferring, use secure methods (e.g., encrypted storage).
- **LLM Output Validation**: Since we use LLMs, note that they can occasionally produce incorrect or hallucinated data. We mitigated this by focusing them on a specific extraction task and validating the output format. But always consider that an AI could mis-label something. Important decisions shouldn’t be made on the AI’s output alone without some human review, especially early on. As we refine, this risk diminishes, but it’s worth stating.
- **Regulatory Compliance**: being a bank means Tech Risk Management (TRM) guidelines apply. Running this as an experimental system locally is fine, but if it moves to production, it will need proper approval, security review, etc. The MVP is a sandbox.
- **Audit Logs**: n8n logs executions which can serve as an audit of data processing. Neo4j logs queries (in Aura you can’t see them, but in an enterprise version you could). For now, if questions arise like “From where did we get this data point?”, we rely on the `source` and `url` on each relationship. That’s our audit trail – you can trace every edge back to origin.

## 14. Folder Structure and Backup

Maintaining an organized folder structure will help manage the various components. Here’s a recommended structure (which mirrors our repository):

```
UHNW_Project/
├── n8n_workflows/           # Exports of n8n workflows (.json) for backup
├── MAS/                     # MAS crawling notebooks or scripts
│   └── MAS_ORG_NER.ipynb
├── SGX Annual Reports/      # SGX PDF processing scripts
│   ├── sgx_ner_pipeline_notebook.ipynb
│   └── sgx_ner_to_neo4j.py
├── WikiData/                # Scripts for Wikidata queries (if any)
├── Ranking/                 # Forbes list and related scripts
│   └── forbes_top50_2025.csv (for example)
├── Neo4j/                   # Graph loading and schema scripts
│   ├── load_graph_v_5.py
│   ├── batch_dedup.py
│   └── schema.cypher        # (maybe constraints and indexes)
├── .env                     # Environment variables (Neo4j URI, keys, etc.)
└── requirements.txt         # Python dependencies
```

Make sure this whole folder is included in your backup strategy. 

**Backing up n8n Workflows**:
- Since we use a Docker volume for n8n data, you should periodically back up that volume. You can do: `docker cp n8n:/home/node/.n8n /path/on/host` to copy out the database file with workflows.
- Or, in n8n Editor, for each workflow do **Export** (it downloads a JSON). Save those JSONs in `n8n_workflows` folder as shown. This way, if you ever lost the n8n instance, you can spin up a new one and import the workflows JSON.
- Also note any credentials in n8n aren’t included in workflow export; you’d need to re-create those in a new instance (since we have only a couple, that’s fine).

**Backing up Neo4j Data**:
- Aura Free doesn’t have an official backup, but the data is small, so you can manually export if needed. For example, run a Cypher in Browser to dump all Person, Company, and relationships to CSV (using `CALL apoc.export.csv.all()` if APOC was available – on Aura Free, APOC might not be fully available). Alternatively:
  - `MATCH (p:Person) RETURN p.name, p.score ...` to get all persons.
  - `MATCH (p:Person)-[r:HAS_ROLE_AT]->(c:Company) RETURN p.name, r.role, c.name, r.source, r.as_of`.
  - `MATCH (a:Person)-[f:FAMILY]->(b:Person) RETURN a.name, f.relation, b.name, f.source`.
  - Save those query results.
- Given the MVP nature, backing up the graph can also be done by just re-running the pipelines on demand (since the sources are the primary data). But if some sources go offline or data changes, having a snapshot is good.
- A simple approach: After building the graph, run: `CALL db.schema.visualization()` in Neo4j Browser to see schema, and maybe use the Neo4j Browser “dump to Cypher” tool (if available via Desktop) to get a Cypher script of the data.

**Backup of Files**:
- PDFs downloaded for SGX should be stored (so we know what was parsed).
- Any intermediate outputs (like the JSON from LLM extraction) if saved, keep them until final verification, then they can be discarded or archived.
- The Forbes list CSV is static – keep a copy as it was at time of processing.

It’s wise to use a version control (Git) or at least a cloud storage to keep all these safe. The provided GitHub repo likely contains most of this (except perhaps actual data files due to size or confidentiality). If the repo is private, ensure the next person has access to it or make a zip archive to hand over.

## 15. Additional Tips for a Smooth Handover

- **Documentation & Continuity**: This guide should be kept up-to-date. If you make tweaks (e.g., change the LLM provider, add a new data source), update the relevant section so the next reader isn’t misled.
- **Team Orientation**: For non-technical colleagues, consider a short training session:
  - Show them how to run a workflow in n8n (it’s a simple click, but unfamiliar UI can confuse at first).
  - Demonstrate looking at Neo4j Bloom to find a person’s connections.
  - Emphasize how each part fits together (maybe walk through one example end-to-end: from new data to updated score).
- **Extending the System**: They should know this is an MVP – manual steps still exist. Future improvements could include:
  - Integrating a user interface (a simple dashboard) so RMs don’t need to use Neo4j Browser directly.
  - Adding more data sources (perhaps news articles via RSS feeds and using the LLM to pull out events like IPO or M&A involving individuals).
  - Improving the scoring model with more factors (as hinted in the capstone, maybe incorporate company market cap or do a proper predictive model).
  - Deploying everything to a server so it can run daily without manual intervention.
- **Points of Contact**: If something goes wrong beyond these instructions, who can help? Ideally list a contact (perhaps the technical lead or someone familiar with Python/Neo4j) that the team can reach out to if they get stuck.
- **Testing**: Encourage the team to do a dry run: e.g., pick a known wealthy individual not in the system yet (say a new tech startup millionaire), input their info (maybe simulate via adding a role or family tie), and see if score reflects appropriately. This helps them trust the system and also understand its mechanics.

- **Common Understanding**: Make sure everyone knows *what the system is doing*: it’s not magic, it’s assembling publicly available facts and highlighting people who have many “wealth indicators” (positions of power, relations to rich people). The results assist RMs but do not guarantee someone is UHNW – it’s a lead, not a final decision. This framing helps the business side use it appropriately.

Finally, treat this system as a **living project**. The graph will grow richer over time (especially if more data is added), and the insights should improve. With proper maintenance (running updates, fixing minor issues), this tool can significantly reduce manual research and uncover hidden gems of prospects.