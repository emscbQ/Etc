import os

with open("./failed_products.txt", "w") as t:
    logs = os.listdir("./logs")
    for filename in logs:
        if filename.startswith("edit_failed"):
            account_name = filename.split("_")[3].replace(".txt", "")
            with open(f"./logs/{filename}", "r") as failed_products:
                for line in failed_products.readlines():
                    t.write(f"{account_name}\t{line}")
