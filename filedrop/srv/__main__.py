import filedrop.srv as f_srv

if __name__ == "__main__":
    app = f_srv.create_app()
    app.run(host="localhost", port=5000, debug=bool(f_srv.CONFIG.get_value("debug")))
