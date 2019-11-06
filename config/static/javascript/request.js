export class Request {
    api = "http://192.168.1.116:5000";
    api_key = "test_secret";
    fetching = false;

    get(url) {
        return fetch(this.api + url, {
                method: "GET",
                headers: {
                    "API_KEY": this.api_key
                }
            })
            .then((response) => response.json())
            .then((data) => data)
            .catch((err) => {
                return {
                    "errors": err
                }
            });
    }
    post(url, data) {
        if (this.fetching) {
            return {
                "errors": {
                    "message": "Request has not been processed yet"
                }
            }
        } else {
            this.fetching = true;
            return fetch(this.api + url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "API_KEY": this.api_key,
                    },
                    mode: "cors",
                    body: JSON.stringify(data)
                })
                .then((response) => {
                    this.fetching = false;
                    return response.json()
                })
                .then((data) => data)
                .catch((err) => console.log(err));
        }

    }
    upload(url, data) {
        return fetch(this.api + url, {
                method: "POST",
                headers: {
                    "API_KEY": this.api_key,
                },
                mode: "cors",
                body: data
            })
            .then((response) => response.json())
            .then((data) => data)
            .catch((err) => {
                return {
                    "errors": err
                }
                l
            });
    }
}