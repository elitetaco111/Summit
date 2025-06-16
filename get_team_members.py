import dropbox

ACCESS_TOKEN = 'sl.u.AFuLjTQBl0I1jopvhbdcEVSGFDbqd37NhC45mMcZzr7Jn1o4-INsYQVX5W6Nuwo6QsGOzvytFr-0PcmKU2KQ6OzXQqLpaS67SEMo2XQBdxC6AuYyQdxv0Su7j12L6kW0YtbUM48IfMtHTzlpUwQhJA1au3t2FgR3B1ScZZWWeCob58IfNXZmUpjKQts2GqoyR2OMurRj6l2tBiutCkuikNLdmmzBIgsQJIv9F47bNApNHSiwnjtenA0yqcb4oL_1jNgQu2Z_X-5dxE3a-LwiZbn8Gx6-Bxvb_fcbdBwXJBGZ06SNx6o_H4fIzGLtG9MKTbeSvZV021x0yJ7BYQUucuJE1z_AjaSOvqq7VNDrVQKtWMEPfP0h2qTr9CCL9KUPICDeP9-dgXpg-8-3tZj4-o8O_eRJp3LXnzW4YS-U-NIuNi2pwjENWwhXsKTg4fAGGQjM1jvz0bnU-kyG916HeN1KtNRfN7ep1xRZEbHflqzIQYyknuKUCcJHMjzBOHox5QGvrFXYWm1g-Sv5vyTZctmHnTQ2P3NWZ8JAMfoENWiPj_sEGKA2Tl-o7FroL8HpChu-WBCwSCM7DWTe8HMzlJEtc8vUIwrQ5tbu8KJbhnY-FlOtW00EpQTZ13RL04UQGYyN1bIlInMkJQSruxMHHozXCXt4NzgXKo6x8IOIKaTHg0C_LokYx4JfRWEiNdpIlEOo2ou18LLGNR65b1ShxFxlXA36VF7YS2HyuWGf_8nxbwxzj4xbsZC82j7S8BYVtNQ6XJ_bf7EnJTeYtCsFS_hUb-R3YsjEoJbxEyPdCx-LNZgLToOJfvZVRDC1woWkSdz3YkDsnrKbLFpYb3I4QeO62w59-uPZ3NQ43rv3boJnLLBMsWTLlx5sOtlof7GKpePOktmsAhmRLpfIh4Nr6N4ZuXovg2OseJ78pg2rS-G9kTXQG36fUoc2hSUCWp8dQ5syawpI2_UOmyUzRIPnFkU815lwIZ2J3qn9K2F3IfBXCuV8sjZEX4RKcWHBhfxcz6VxVJOGPufYH-fsERxz1BLb1SgCvZwkk8VVK9akP7PWOfGMhI98IOuv1djvSWX4fJ1qsrHOTSBPU4IqOCWejWsLc5kfI2lKPEKtc5UgS_HkzSMl-Yxma8ZO1JPHKQntdvPLXOztcF4a_ceVvkiExh6f'
OUTPUT_FILE = 'dropbox_structure.txt'
TEAM_MEMBER_ID = 'dbmid:AABAstJwy8C7P-AOJ86w37t70kRPYmZwIvk'

def get_shared_folders_with_namespace_ids(user_dbx):
    shared_folders = []
    result = user_dbx.sharing_list_folders()
    shared_folders.extend(result.entries)

    # Only loop if has_more exists and is True
    while hasattr(result, "has_more") and result.has_more:
        result = user_dbx.sharing_list_folders_continue(result.cursor)
        shared_folders.extend(result.entries)

    for folder in shared_folders:
        print(f"{folder.name} - Shared Folder ID: {folder.shared_folder_id} - Namespace ID: {folder.shared_folder_id}")

    return shared_folders

dbx = dropbox.DropboxTeam(ACCESS_TOKEN)
members = dbx.team_members_list().members
for member in members:
    print(f"{member.profile.email}: {member.profile.team_member_id}")
    user_dbx = dbx.as_user(member.profile.team_member_id)
    get_shared_folders_with_namespace_ids(user_dbx)
