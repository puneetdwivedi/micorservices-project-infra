import express from 'express';
import cors from 'cors';

const app = express();
const PORT = process.env.PRODUCTAPP_PORT || (() => {
    throw new Error("PRODUCTAPP_PORT is not defined");
})();;

const AUTHAPP_URL = process.env.AUTHAPP_URL || (() => {
    throw new Error("AUTHAPP_URL is not defined");
})


app.use(cors());
app.use(express.json());

app.get('/api/product', (req, res) => {
    res.json({ message: 'Products service is running!' });
});

app.get('/api/products/:productId', (req, res)=>{
    const productId = req.params.productId;
    const products =  [
        { id: '1', name: 'Laptop', price: 999 },
        { id: '2', name: 'Smartphone', price: 499 },
        { id: '3', name: 'Headphones', price: 199 }
    ];
    const product = products.find(p => p.id === productId);
    if (product) {
        res.json(product);
    } else {
        res.status(404).json({ error: 'Product not found' });
    }
})

app.get('/api/products/cart/:userId', (req, res) => {   
    const userId = req.params.userId; 


    fetch(`${AUTHAPP_URL}/api/auth/users/${userId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('User not found');
            }
            return response.json();
        })
        .then(userData => {
            // For simplicity, we return a static cart for the user
            const cart = {
                user: userData,
                items: [
                    { productId: '1', quantity: 1 },
                    { productId: '2', quantity: 2 }
                ]
            };
            res.json(cart);
        })
        .catch(error => {
            res.status(404).json({ error: error.message });
        });

})


app.listen(PORT, () => {
    console.log(`Products service is running on port ${PORT}`);
});
