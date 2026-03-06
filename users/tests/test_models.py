from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import SpotifyToken

User = get_user_model()


class UserModelTests(TestCase):

    # -------------------------
    # Role field defaults
    # -------------------------

    def test_user_default_role_is_user(self):
        user = User.objects.create_user(username="alice", password="pass123")
        self.assertEqual(user.role, "user")

    def test_user_role_can_be_set_to_manager(self):
        user = User.objects.create_user(username="bob", password="pass123", role="manager")
        self.assertEqual(user.role, "manager")

    def test_user_role_can_be_set_to_admin(self):
        user = User.objects.create_user(username="carol", password="pass123", role="admin")
        self.assertEqual(user.role, "admin")

    # -------------------------
    # __str__ representation
    # -------------------------

    def test_user_str_includes_username_and_role(self):
        user = User.objects.create_user(username="dave", password="pass123", role="manager")
        self.assertEqual(str(user), "dave (manager)")

    def test_user_str_default_role(self):
        user = User.objects.create_user(username="eve", password="pass123")
        self.assertEqual(str(user), "eve (user)")

    # -------------------------
    # Unusable password (Spotify users)
    # -------------------------

    def test_spotify_user_has_unusable_password(self):
        user = User.objects.create_user(username="spotifyuser", password="temp")
        user.set_unusable_password()
        user.save()
        self.assertFalse(user.has_usable_password())

    def test_regular_user_has_usable_password(self):
        user = User.objects.create_user(username="regularuser", password="pass123")
        self.assertTrue(user.has_usable_password())

    # -------------------------
    # Username uniqueness
    # -------------------------

    def test_duplicate_username_raises_error(self):
        User.objects.create_user(username="uniqueuser", password="pass123")
        with self.assertRaises(Exception):
            User.objects.create_user(username="uniqueuser", password="pass456")

    # -------------------------
    # Email field
    # -------------------------

    def test_user_email_stored_correctly(self):
        user = User.objects.create_user(username="frank", password="pass123", email="frank@example.com")
        self.assertEqual(user.email, "frank@example.com")

    def test_user_email_can_be_blank(self):
        user = User.objects.create_user(username="nomail", password="pass123", email="")
        self.assertEqual(user.email, "")


class SpotifyTokenModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="tokenuser", password="pass123")

    # -------------------------
    # Token creation
    # -------------------------

    def test_spotify_token_created_for_user(self):
        token = SpotifyToken.objects.create(
            user=self.user,
            access_token="access_abc",
            refresh_token="refresh_xyz",
            expires_at=9999999999,
        )
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.access_token, "access_abc")
        self.assertEqual(token.refresh_token, "refresh_xyz")
        self.assertEqual(token.expires_at, 9999999999)

    # -------------------------
    # OneToOne enforcement
    # -------------------------

    def test_one_user_can_only_have_one_spotify_token(self):
        SpotifyToken.objects.create(
            user=self.user,
            access_token="access_abc",
            refresh_token="refresh_xyz",
            expires_at=9999999999,
        )
        with self.assertRaises(Exception):
            SpotifyToken.objects.create(
                user=self.user,
                access_token="access_second",
                refresh_token="refresh_second",
                expires_at=1111111111,
            )

    # -------------------------
    # Cascade delete
    # -------------------------

    def test_spotify_token_deleted_when_user_deleted(self):
        SpotifyToken.objects.create(
            user=self.user,
            access_token="access_abc",
            refresh_token="refresh_xyz",
            expires_at=9999999999,
        )
        user_id = self.user.id
        self.user.delete()
        self.assertFalse(SpotifyToken.objects.filter(user_id=user_id).exists())

    # -------------------------
    # update_or_create (mirrors spotify_callback logic)
    # -------------------------

    def test_update_or_create_token_updates_existing(self):
        SpotifyToken.objects.create(
            user=self.user,
            access_token="old_access",
            refresh_token="old_refresh",
            expires_at=1000,
        )
        SpotifyToken.objects.update_or_create(
            user=self.user,
            defaults={
                "access_token": "new_access",
                "refresh_token": "new_refresh",
                "expires_at": 9999999999,
            }
        )
        token = SpotifyToken.objects.get(user=self.user)
        self.assertEqual(token.access_token, "new_access")
        self.assertEqual(token.refresh_token, "new_refresh")

    def test_update_or_create_token_creates_if_missing(self):
        SpotifyToken.objects.update_or_create(
            user=self.user,
            defaults={
                "access_token": "brand_new",
                "refresh_token": "brand_refresh",
                "expires_at": 9999999999,
            }
        )
        self.assertTrue(SpotifyToken.objects.filter(user=self.user).exists())