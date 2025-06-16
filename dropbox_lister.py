import dropbox

ACCESS_TOKEN = 'sl.u.AFuLjTQBl0I1jopvhbdcEVSGFDbqd37NhC45mMcZzr7Jn1o4-INsYQVX5W6Nuwo6QsGOzvytFr-0PcmKU2KQ6OzXQqLpaS67SEMo2XQBdxC6AuYyQdxv0Su7j12L6kW0YtbUM48IfMtHTzlpUwQhJA1au3t2FgR3B1ScZZWWeCob58IfNXZmUpjKQts2GqoyR2OMurRj6l2tBiutCkuikNLdmmzBIgsQJIv9F47bNApNHSiwnjtenA0yqcb4oL_1jNgQu2Z_X-5dxE3a-LwiZbn8Gx6-Bxvb_fcbdBwXJBGZ06SNx6o_H4fIzGLtG9MKTbeSvZV021x0yJ7BYQUucuJE1z_AjaSOvqq7VNDrVQKtWMEPfP0h2qTr9CCL9KUPICDeP9-dgXpg-8-3tZj4-o8O_eRJp3LXnzW4YS-U-NIuNi2pwjENWwhXsKTg4fAGGQjM1jvz0bnU-kyG916HeN1KtNRfN7ep1xRZEbHflqzIQYyknuKUCcJHMjzBOHox5QGvrFXYWm1g-Sv5vyTZctmHnTQ2P3NWZ8JAMfoENWiPj_sEGKA2Tl-o7FroL8HpChu-WBCwSCM7DWTe8HMzlJEtc8vUIwrQ5tbu8KJbhnY-FlOtW00EpQTZ13RL04UQGYyN1bIlInMkJQSruxMHHozXCXt4NzgXKo6x8IOIKaTHg0C_LokYx4JfRWEiNdpIlEOo2ou18LLGNR65b1ShxFxlXA36VF7YS2HyuWGf_8nxbwxzj4xbsZC82j7S8BYVtNQ6XJ_bf7EnJTeYtCsFS_hUb-R3YsjEoJbxEyPdCx-LNZgLToOJfvZVRDC1woWkSdz3YkDsnrKbLFpYb3I4QeO62w59-uPZ3NQ43rv3boJnLLBMsWTLlx5sOtlof7GKpePOktmsAhmRLpfIh4Nr6N4ZuXovg2OseJ78pg2rS-G9kTXQG36fUoc2hSUCWp8dQ5syawpI2_UOmyUzRIPnFkU815lwIZ2J3qn9K2F3IfBXCuV8sjZEX4RKcWHBhfxcz6VxVJOGPufYH-fsERxz1BLb1SgCvZwkk8VVK9akP7PWOfGMhI98IOuv1djvSWX4fJ1qsrHOTSBPU4IqOCWejWsLc5kfI2lKPEKtc5UgS_HkzSMl-Yxma8ZO1JPHKQntdvPLXOztcF4a_ceVvkiExh6f'
OUTPUT_FILE = 'dropbox_structure.txt'
TEAM_MEMBER_ID = 'dbmid:AABAstJwy8C7P-AOJ86w37t70kRPYmZwIvk'

def list_folder(dbx, path="", indent=0, file_handle=None):
    try:
        res = dbx.files_list_folder(path)
        for entry in res.entries:
            print(" " * indent, entry.name)  # Debug: print every entry
            if isinstance(entry, dropbox.files.FolderMetadata):
                file_handle.write("    " * indent + f"[Folder] {entry.name}\n")
                try:
                    list_folder(dbx, entry.path_lower, indent + 1, file_handle)
                except Exception as e:
                    print(f"Error listing subfolder {entry.path_lower}: {e}")
            elif isinstance(entry, dropbox.files.FileMetadata):
                file_handle.write("    " * indent + f"{entry.name}\n")
        while res.has_more:
            res = dbx.files_list_folder_continue(res.cursor)
            for entry in res.entries:
                print(" " * indent, entry.name)  # Debug: print every entry
                if isinstance(entry, dropbox.files.FolderMetadata):
                    file_handle.write("    " * indent + f"[Folder] {entry.name}\n")
                    try:
                        list_folder(dbx, entry.path_lower, indent + 1, file_handle)
                    except Exception as e:
                        print(f"Error listing subfolder {entry.path_lower}: {e}")
                elif isinstance(entry, dropbox.files.FileMetadata):
                    file_handle.write("    " * indent + f"{entry.name}\n")
    except Exception as e:
        print(f"Error listing folder {path}: {e}")

def main():
    team_dbx = dropbox.DropboxTeam(ACCESS_TOKEN)
    dbx = team_dbx.as_user(TEAM_MEMBER_ID)
    start_path = ""  # List root
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        list_folder(dbx, start_path, 0, f)
    print(f"Dropbox structure written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()