"""
Email Templates for FreelanceHub Monetization
==============================================
HTML email templates for subscription confirmations,
payment receipts, and withdrawal notifications.
"""


def subscription_confirmation_email(user_name, plan_name, plan_price, features):
    """Generate HTML email for subscription confirmation."""
    features_html = ""
    for key, value in features.items():
        if value is True:
            features_html += f'<li style="padding:6px 0;color:#333;">✅ {key.replace("_", " ").title()}</li>'
        elif value is False:
            continue
        elif value == 'unlimited':
            features_html += f'<li style="padding:6px 0;color:#333;">♾️ {key.replace("_", " ").title()} illimité</li>'
        else:
            features_html += f'<li style="padding:6px 0;color:#333;">✅ {key.replace("_", " ").title()}: {value}</li>'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f4f0ff;">
        <table cellpadding="0" cellspacing="0" width="100%" style="max-width:600px;margin:40px auto;">
            <tr>
                <td style="background:linear-gradient(135deg,#7c3aed,#a855f7);padding:40px 30px;border-radius:16px 16px 0 0;text-align:center;">
                    <h1 style="color:#fff;margin:0 0 8px;font-size:24px;">🎉 Bienvenue dans {plan_name} !</h1>
                    <p style="color:rgba(255,255,255,0.9);margin:0;font-size:14px;">Votre abonnement FreelanceHub est actif</p>
                </td>
            </tr>
            <tr>
                <td style="background:#fff;padding:30px;border-radius:0 0 16px 16px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
                    <p style="color:#333;font-size:16px;margin:0 0 20px;">Bonjour <strong>{user_name}</strong>,</p>
                    <p style="color:#666;font-size:14px;line-height:1.6;margin:0 0 20px;">
                        Merci pour votre abonnement au plan <strong>{plan_name}</strong>.
                        Votre compte a été mis à niveau et vous pouvez dès maintenant profiter de toutes les fonctionnalités premium.
                    </p>

                    <div style="background:#f8f5ff;border:1px solid #e9e0ff;border-radius:12px;padding:20px;margin:0 0 24px;">
                        <h3 style="margin:0 0 12px;color:#7c3aed;font-size:16px;">Détails de l'abonnement</h3>
                        <table cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td style="padding:6px 0;color:#666;font-size:13px;">Plan</td>
                                <td style="padding:6px 0;color:#333;font-size:13px;text-align:right;font-weight:600;">{plan_name}</td>
                            </tr>
                            <tr>
                                <td style="padding:6px 0;color:#666;font-size:13px;">Montant</td>
                                <td style="padding:6px 0;color:#333;font-size:13px;text-align:right;font-weight:600;">{plan_price}€/mois</td>
                            </tr>
                            <tr>
                                <td style="padding:6px 0;color:#666;font-size:13px;">Renouvellement</td>
                                <td style="padding:6px 0;color:#333;font-size:13px;text-align:right;font-weight:600;">Automatique</td>
                            </tr>
                        </table>
                    </div>

                    <h3 style="margin:0 0 12px;color:#333;font-size:15px;">Vos avantages :</h3>
                    <ul style="list-style:none;padding:0;margin:0 0 24px;">
                        {features_html}
                    </ul>

                    <div style="text-align:center;margin:24px 0;">
                        <a href="https://freelancehub.app/pricing"
                           style="display:inline-block;background:linear-gradient(135deg,#7c3aed,#a855f7);color:#fff;
                                  text-decoration:none;padding:14px 32px;border-radius:12px;font-weight:600;font-size:14px;">
                            Accéder à mon compte
                        </a>
                    </div>

                    <p style="color:#999;font-size:12px;margin:20px 0 0;text-align:center;line-height:1.5;">
                        Vous pouvez annuler votre abonnement à tout moment depuis les paramètres de votre compte.
                        <br>© 2026 FreelanceHub. Tous droits réservés.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def payment_receipt_email(user_name, amount, transaction_type, transaction_id, commission=0, net_amount=0):
    """Generate HTML email for payment receipt."""
    type_labels = {
        'project': 'Projet',
        'store': 'Produit Digital',
        'service': 'Service',
        'boost': 'Mise en avant',
        'premium_feature': 'Fonctionnalité Premium',
        'subscription': 'Abonnement'
    }
    type_label = type_labels.get(transaction_type, transaction_type)

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f4f0ff;">
        <table cellpadding="0" cellspacing="0" width="100%" style="max-width:600px;margin:40px auto;">
            <tr>
                <td style="background:linear-gradient(135deg,#10b981,#06b6d4);padding:30px;border-radius:16px 16px 0 0;text-align:center;">
                    <h1 style="color:#fff;margin:0 0 4px;font-size:20px;">Reçu de paiement</h1>
                    <p style="color:rgba(255,255,255,0.9);margin:0;font-size:13px;">Transaction #{transaction_id[:8]}</p>
                </td>
            </tr>
            <tr>
                <td style="background:#fff;padding:30px;border-radius:0 0 16px 16px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
                    <p style="color:#333;font-size:15px;margin:0 0 20px;">Bonjour <strong>{user_name}</strong>,</p>
                    <p style="color:#666;font-size:14px;line-height:1.6;margin:0 0 20px;">
                        Votre paiement a été traité avec succès. Voici le récapitulatif :
                    </p>

                    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;padding:20px;margin:0 0 24px;">
                        <table cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td style="padding:8px 0;color:#666;font-size:13px;">Type</td>
                                <td style="padding:8px 0;color:#333;font-size:13px;text-align:right;font-weight:600;">{type_label}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px 0;color:#666;font-size:13px;">Montant brut</td>
                                <td style="padding:8px 0;color:#333;font-size:13px;text-align:right;font-weight:600;">{amount}€</td>
                            </tr>
                            <tr>
                                <td style="padding:8px 0;color:#666;font-size:13px;">Commission plateforme</td>
                                <td style="padding:8px 0;color:#ef4444;font-size:13px;text-align:right;font-weight:600;">-{commission}€</td>
                            </tr>
                            <tr style="border-top:1px solid #d1fae5;">
                                <td style="padding:12px 0 0;color:#333;font-size:15px;font-weight:700;">Montant net</td>
                                <td style="padding:12px 0 0;color:#10b981;font-size:18px;text-align:right;font-weight:800;">{net_amount}€</td>
                            </tr>
                        </table>
                    </div>

                    <p style="color:#999;font-size:12px;margin:20px 0 0;text-align:center;">
                        © 2026 FreelanceHub. Tous droits réservés.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def withdrawal_notification_email(user_name, amount, fee, net_amount, method, estimated_date):
    """Generate HTML email for withdrawal notification."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f4f0ff;">
        <table cellpadding="0" cellspacing="0" width="100%" style="max-width:600px;margin:40px auto;">
            <tr>
                <td style="background:linear-gradient(135deg,#f59e0b,#fbbf24);padding:30px;border-radius:16px 16px 0 0;text-align:center;">
                    <h1 style="color:#fff;margin:0 0 4px;font-size:20px;">💸 Retrait en cours</h1>
                </td>
            </tr>
            <tr>
                <td style="background:#fff;padding:30px;border-radius:0 0 16px 16px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
                    <p style="color:#333;font-size:15px;margin:0 0 20px;">Bonjour <strong>{user_name}</strong>,</p>
                    <p style="color:#666;font-size:14px;line-height:1.6;margin:0 0 20px;">
                        Votre demande de retrait a été reçue et est en cours de traitement.
                    </p>

                    <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:12px;padding:20px;">
                        <table cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                                <td style="padding:6px 0;color:#666;font-size:13px;">Montant demandé</td>
                                <td style="padding:6px 0;color:#333;font-size:13px;text-align:right;font-weight:600;">{amount}€</td>
                            </tr>
                            <tr>
                                <td style="padding:6px 0;color:#666;font-size:13px;">Frais</td>
                                <td style="padding:6px 0;color:#333;font-size:13px;text-align:right;">-{fee}€</td>
                            </tr>
                            <tr>
                                <td style="padding:6px 0;color:#666;font-size:13px;">Montant net</td>
                                <td style="padding:6px 0;color:#10b981;font-size:15px;text-align:right;font-weight:700;">{net_amount}€</td>
                            </tr>
                            <tr>
                                <td style="padding:6px 0;color:#666;font-size:13px;">Méthode</td>
                                <td style="padding:6px 0;color:#333;font-size:13px;text-align:right;">{method}</td>
                            </tr>
                            <tr>
                                <td style="padding:6px 0;color:#666;font-size:13px;">Date estimée</td>
                                <td style="padding:6px 0;color:#333;font-size:13px;text-align:right;font-weight:600;">{estimated_date}</td>
                            </tr>
                        </table>
                    </div>

                    <p style="color:#999;font-size:12px;margin:20px 0 0;text-align:center;">
                        © 2026 FreelanceHub. Tous droits réservés.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
